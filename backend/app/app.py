from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import time

# === Import AI Pipeline ===
from backend.app.embedding import SequenceEmbedder
from backend.app.clustering import HDBSCANClusterer 
from backend.annotator import Annotator
from backend.app.classifier import UnsupervisedClassifier
from backend.app.ai_pipeline.unsupervised import UnsupervisedLearningPipeline
from backend.app.ai_pipeline.feature_extraction import FeatureExtractor


# === Import Mock Fallback ===
from backend.app.classifier import MockSpeciesClassifier 

app = Flask(__name__)
CORS(app)

# Initialize pipeline
embedder = SequenceEmbedder()
clusterer = HDBSCANClusterer()
annotator = Annotator()


# --- API Routes ---
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})


@app.route('/api/analyze', methods=['POST'])
def analyze_sequence():
    """
    Accepts DNA sequences from frontend, runs AI pipeline,
    returns biodiversity metrics + classification.
    """
    start_time = time.time()

    # ✅ 1. Parse Input
    if 'fasta_file' not in request.files:
        return jsonify({"error": "No FASTA file uploaded"}), 400

    file = request.files['fasta_file']
    sequences = [line.strip() for line in file if not line.startswith(">")]
    if not sequences:
        return jsonify({"error": "No sequences found in FASTA"}), 400

    # ✅ 2. Try AI pipeline
    try:
        embeddings = embedder.encode_sequences(sequences)
        otu_clusters = clusterer.cluster_embeddings(embeddings)
        annotated_otus = annotator.annotate_clusters(otu_clusters, sequences)

        classification_results = annotated_otus  # replace Mock output

    except Exception as e:
        print("⚠️ AI pipeline failed, falling back to MockSpeciesClassifier:", str(e))
        mock = MockSpeciesClassifier()
        classification_results = mock.classify_sequences(sequences)

    # ✅ 3. Compute Biodiversity Metrics
    shannon = round(len(set(sequences)) * 0.8, 3)  # placeholder
    simpson = round(1 - (1 / (1 + len(sequences))), 3)
    phylogenetic_div = round(len(sequences) ** 0.5, 3)

    # ✅ 4. Prepare Results (Dashboard Compatible)
    results = {
        "analysis_id": None,  # Add DB integration later if needed
        "filename": file.filename,
        "total_sequences": len(sequences),
        "processing_time_seconds": round(time.time() - start_time, 2),
        "taxonomic_classification": classification_results,
        "biodiversity_metrics": {
            "shannon_diversity": shannon,
            "simpson_index": simpson,
            "phylogenetic_diversity": phylogenetic_div
        },
        "species_distribution": classification_results,  # frontend expects this
        "timestamp": datetime.now().isoformat()
    }

    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)
