"""
eDNA Biodiversity Analysis Platform
Smart India Hackathon 2025 - Problem SIH25042
Ministry of Earth Sciences
"""

import os
import sys
import time
import sqlite3
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Fixed imports - use relative imports within backend package
from .file_processor import FastaProcessor
from .classifier import MockSpeciesClassifier
from .biodiversity import BiodiversityCalculator
from .database import DatabaseManager

# Correct paths for templates and static
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/static'))

# If your app.py is inside backend/app/
# ../../ means: backend/app → backend → edna-biodiversity-platform


# then into frontend/templates ✅



# template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/templates'))
# static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)





# Configuration
app.config['UPLOAD_FOLDER'] = '../frontend/static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'fasta', 'fa', 'fas', 'txt'}

# Enable CORS for API endpoints
CORS(app)

# Initialize components
db_manager = DatabaseManager()
fasta_processor = FastaProcessor()
classifier = MockSpeciesClassifier()
biodiversity_calc = BiodiversityCalculator()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/upload')
def upload_page():
    """File upload page"""
    return render_template('upload.html')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_sequences():
    """
    Main analysis endpoint - processes FASTA file and returns biodiversity metrics
    Expected to handle 1,000 sequences in under 30 seconds
    """
    start_time = time.time()
    
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload FASTA files (.fasta, .fa, .fas, .txt)'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process FASTA file
        sequences = fasta_processor.parse_fasta(filepath)
        total_sequences = len(sequences)
        
        if total_sequences == 0:
            return jsonify({'error': 'No valid sequences found in file'}), 400
        
        # Perform species classification (mock)
        classification_results = classifier.classify_sequences(sequences)
        
        # Calculate biodiversity metrics
        biodiversity_metrics = biodiversity_calc.calculate_metrics(classification_results)
        
        # Store results in database
        analysis_id = db_manager.store_analysis_results(
            filename, total_sequences, classification_results, biodiversity_metrics
        )
        
        processing_time = time.time() - start_time
        
        # Prepare response
        response = {
            'analysis_id': analysis_id,
            'filename': filename,
            'total_sequences': total_sequences,
            'processing_time_seconds': round(processing_time, 2),
            'taxonomic_classification': classification_results,
            'biodiversity_metrics': biodiversity_metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

logger = logging.getLogger(__name__)

@app.route('/api/dashboard-data')
def dashboard_data():
    """Get aggregated data for dashboard visualization"""
    try:
        # Get recent analyses
        recent_analyses = db_manager.get_recent_analyses(limit=10)
        
        # Get species distribution data
        species_distribution = db_manager.get_species_distribution()
        
        # Get biodiversity trends
        biodiversity_trends = db_manager.get_biodiversity_trends()
        
        return jsonify({
            'recent_analyses': recent_analyses,
            'species_distribution': species_distribution,
            'biodiversity_trends': biodiversity_trends,
            'summary_stats': {
                'total_analyses': db_manager.get_total_analyses(),
                'total_species_identified': db_manager.get_total_species_count(),
                'average_diversity_index': db_manager.get_average_diversity()
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch dashboard data: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch dashboard data: {str(e)}'}), 500

@app.route('/api/analysis/<int:analysis_id>')
def get_analysis(analysis_id):
    """Get specific analysis results"""
    try:
        analysis = db_manager.get_analysis_by_id(analysis_id)
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Failed to fetch analysis {analysis_id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch analysis: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize database
    db_manager.init_database()
    
    # Start development server
    app.run(host='0.0.0.0', port=5000, debug=True)