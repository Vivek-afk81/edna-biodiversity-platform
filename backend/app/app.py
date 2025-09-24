import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blast_helper import BlastHelper
from models import get_database

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import time

# === Import AI Pipeline ===
from backend.app.embedding import SequenceEmbedder
from backend.app.clustering import HDBSCANClusterer 
from backend.annotator import Annotator

# === Import Mock Fallback ===
# from backend.app.classifier import MockSpeciesClassifier 
from backend.app.classifier import classify_sequences_fallback


app = Flask(__name__)
CORS(app)

# Initialize components
embedder = SequenceEmbedder()
clusterer = HDBSCANClusterer(min_cluster_size=2, min_samples=1)
annotator = Annotator()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

@app.before_first_request
def create_database():
    """Create our database when the app starts"""
    print("Setting up the database...")
    session, engine = get_database()
    session.close()
    print("Database ready!")

@app.route('/api/analyze', methods=['POST'])
def analyze_sequence():
    """
    Accepts DNA sequences from frontend, runs AI pipeline,
    returns biodiversity metrics + classification.
    """
    start_time = time.time()

    # 1. Parse Input
    if 'fasta_file' not in request.files:
        return jsonify({"error": "No FASTA file uploaded"}), 400

    file = request.files['fasta_file']
    # Read lines, decode bytes to str if necessary
    content = file.read().decode('utf-8').splitlines()
    sequences = [line.strip() for line in content if line and not line.startswith(">")]
    if not sequences:
        return jsonify({"error": "No sequences found in FASTA"}), 400

    # 2. Try AI pipeline
    try:
        # 2a. Generate embeddings
        embeddings = embedder.encode_sequences(sequences)

        # 2b. Cluster embeddings into OTUs
        cluster_labels = clusterer.fit_predict(embeddings)
        clusters = {}
        for idx, label in enumerate(cluster_labels):
            if label == -1:
                continue  # skip noise
            key = f"OTU_{label}"
            clusters.setdefault(key, []).append(idx)

        # 2c. Annotate clusters
        annotated_otus = annotator.annotate_clusters(clusters, sequences)
        classification_results = annotated_otus

    except Exception as e:
        print("⚠️ AI pipeline failed, falling back to MockSpeciesClassifier:", str(e))
        classification_results = classify_sequences_fallback([{"sequence": seq} for seq in sequences])


    # 3. Compute Biodiversity Metrics
    unique_count = len(set(sequences))
    total = len(sequences)
    shannon = round(unique_count * 0.8, 3)   # placeholder
    simpson = round(1 - (1 / (1 + total)), 3)
    phylogenetic_div = round(total ** 0.5, 3)

    # 4. Prepare Results
    results = {
        "analysis_id": None,
        "filename": file.filename,
        "total_sequences": total,
        "processing_time_seconds": round(time.time() - start_time, 2),
        "taxonomic_classification": classification_results,
        "biodiversity_metrics": {
            "shannon_diversity": shannon,
            "simpson_index": simpson,
            "phylogenetic_diversity": phylogenetic_div
        },
        "species_distribution": classification_results,
        "timestamp": datetime.now().isoformat()
    }

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
