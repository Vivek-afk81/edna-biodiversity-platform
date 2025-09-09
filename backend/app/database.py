import sqlite3
import json
import threading
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Use environment variable or default to project database directory
            db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'database')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'edna_biodiversity.db')

        self.db_path = db_path
        self.lock = threading.Lock()

        # Performance optimization settings
        self.pragma_settings = [
            "PRAGMA journal_mode = WAL",
            "PRAGMA synchronous = NORMAL",
            "PRAGMA cache_size = 10000",
            "PRAGMA temp_store = MEMORY",
            "PRAGMA mmap_size = 268435456",
        ]

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row

            for pragma in self.pragma_settings:
                conn.execute(pragma)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def init_database(self):
        """Initialize database tables and indexes"""
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Analyses table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analyses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        processing_time_seconds REAL,
                        total_sequences INTEGER,
                        unique_taxa_count INTEGER,
                        novel_species_count INTEGER,
                        shannon_index REAL,
                        simpson_index REAL,
                        evenness_index REAL,
                        status TEXT DEFAULT 'completed',
                        metadata TEXT
                    )
                ''')

                # Species classifications table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS species_classifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id INTEGER,
                        sequence_id TEXT,
                        predicted_taxon TEXT,
                        confidence REAL,
                        taxonomic_rank TEXT,
                        ecological_role TEXT,
                        gc_content REAL,
                        sequence_length INTEGER,
                        quality_score REAL,
                        FOREIGN KEY (analysis_id) REFERENCES analyses (id)
                    )
                ''')

                # Species abundance table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS species_abundance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id INTEGER,
                        species_name TEXT,
                        sequence_count INTEGER,
                        percentage REAL,
                        is_novel_species BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (analysis_id) REFERENCES analyses (id)
                    )
                ''')

                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyses_timestamp ON analyses(upload_timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_species_analysis_id ON species_classifications(analysis_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_abundance_analysis_id ON species_abundance(analysis_id)')

                conn.commit()

    def store_analysis_results(self, filename: str, total_sequences: int, classification_results: Dict, biodiversity_metrics: Dict) -> int:
        """Store analysis results with proper error handling and transaction management"""
        if not isinstance(total_sequences, int) or total_sequences < 0:
            raise ValueError("Invalid total_sequences value")
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Invalid filename")

        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                try:
                    # Start transaction
                    cursor.execute("BEGIN TRANSACTION")

                    processing_time = total_sequences * 0.02
                    indices = biodiversity_metrics.get('indices', {})

                    cursor.execute('''
                        INSERT INTO analyses (
                            filename, total_sequences, unique_taxa_count, novel_species_count,
                            shannon_index, simpson_index, evenness_index, processing_time_seconds, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        filename.strip(),
                        total_sequences,
                        classification_results.get('unique_taxa_identified', 0),
                        classification_results.get('novel_species_discovered', 0),
                        indices.get('shannon_diversity', 0),
                        indices.get('simpson_diversity', 0),
                        indices.get('shannon_evenness', 0),
                        processing_time,
                        json.dumps(biodiversity_metrics)
                    ))

                    analysis_id = cursor.lastrowid

                    # Store classifications with validation
                    classified_sequences = classification_results.get('classified_sequences', [])
                    for seq_result in classified_sequences:
                        if not isinstance(seq_result, dict):
                            continue

                        cursor.execute('''
                            INSERT INTO species_classifications (
                                analysis_id, sequence_id, predicted_taxon, confidence,
                                taxonomic_rank, ecological_role, gc_content,
                                sequence_length, quality_score
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            analysis_id,
                            seq_result.get('sequence_id', ''),
                            seq_result.get('predicted_taxon', 'Unknown'),
                            max(0.0, min(1.0, seq_result.get('confidence', 0.0))),  # Clamp confidence to [0,1]
                            seq_result.get('taxonomic_rank', 'Unknown'),
                            seq_result.get('ecological_role', 'Unknown'),
                            seq_result.get('gc_content', 0.0),
                            seq_result.get('sequence_length', 0),
                            seq_result.get('quality_score', 0.0)
                        ))

                    # Store abundance with validation
                    species_distribution = classification_results.get('species_distribution', {})
                    for species, count in species_distribution.items():
                        if not isinstance(count, (int, float)) or count < 0:
                            continue

                        percentage = (count / total_sequences) * 100 if total_sequences > 0 else 0
                        is_novel = any(keyword in str(species).lower() for keyword in ['unknown', 'novel', 'mystery'])

                        cursor.execute('''
                            INSERT INTO species_abundance (
                                analysis_id, species_name, sequence_count, percentage, is_novel_species
                            ) VALUES (?, ?, ?, ?, ?)
                        ''', (analysis_id, str(species), int(count), percentage, is_novel))

                    # Commit transaction
                    conn.commit()
                    return analysis_id

                except Exception as e:
                    conn.rollback()
                    raise RuntimeError(f"Failed to store analysis results: {str(e)}") from e

    def get_recent_analyses(self, limit: int = 10) -> List[Dict]:
        """Get recent analyses with input validation"""
        if not isinstance(limit, int) or limit <= 0 or limit > 100:
            limit = 10

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, filename, upload_timestamp, total_sequences,
                       unique_taxa_count, novel_species_count, shannon_index
                FROM analyses
                ORDER BY upload_timestamp DESC
                LIMIT ?
            ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_species_distribution(self) -> List[Dict]:
        """Get species distribution data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT species_name, SUM(sequence_count) as total_count,
                       AVG(percentage) as avg_percentage
                FROM species_abundance
                GROUP BY species_name
                ORDER BY total_count DESC
                LIMIT 15
            ''')

            return [dict(row) for row in cursor.fetchall()]

    def get_biodiversity_trends(self) -> Dict:
        """Get biodiversity trends data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DATE(upload_timestamp) as date,
                       AVG(shannon_index) as avg_shannon,
                       COUNT(*) as analyses_count
                FROM analyses
                WHERE upload_timestamp >= datetime('now', '-30 days')
                GROUP BY DATE(upload_timestamp)
                ORDER BY date
            ''')

            rows = cursor.fetchall()
            return {
                'dates': [row['date'] for row in rows],
                'shannon_values': [row['avg_shannon'] or 0 for row in rows],
                'analyses_counts': [row['analyses_count'] for row in rows]
            }

    def get_analysis_by_id(self, analysis_id: int) -> Optional[Dict]:
        """Get analysis by ID with validation"""
        if not isinstance(analysis_id, int) or analysis_id <= 0:
            return None

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_total_analyses(self) -> int:
        """Get total number of analyses"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM analyses')
            return cursor.fetchone()[0]

    def get_total_species_count(self) -> int:
        """Get total number of unique species"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(DISTINCT species_name) FROM species_abundance')
            result = cursor.fetchone()[0]
            return result if result else 0

    def get_average_diversity(self) -> float:
        """Get average Shannon diversity index"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT AVG(shannon_index) FROM analyses')
            result = cursor.fetchone()[0]
            return round(result, 3) if result else 0.0
