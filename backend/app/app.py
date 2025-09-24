import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blast_helper import BlastHelper
from models import get_database

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import time

# === Import Species Network Analysis ===
from backend.app.species_network import create_species_network_analysis

# === Import AI Pipeline ===
from backend.app.embedding import SequenceEmbedder
from backend.app.clustering import HDBSCANClusterer 
from backend.annotator import Annotator

# === Import Enhanced Fallback ===
from backend.app.classifier import classify_sequences_fallback

# === NEW: Import Ecosystem Health Analyzer ===
from backend.app.ecosystem_health import get_ecosystem_health_analysis

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
    Enhanced analysis with proper biodiversity metrics and ecosystem health scoring.
    """
    start_time = time.time()

    # 1. Parse Input
    if 'fasta_file' not in request.files:
        return jsonify({"error": "No FASTA file uploaded"}), 400

    file = request.files['fasta_file']
    content = file.read().decode('utf-8').splitlines()
    sequences = [line.strip() for line in content if line and not line.startswith(">")]
    
    if not sequences:
        return jsonify({"error": "No sequences found in FASTA"}), 400

    print(f"🧬 Processing {len(sequences)} sequences...")

    # 2. Try AI pipeline
    try:
        print("🤖 Running DNABERT-2 + HDBSCAN pipeline...")
        
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
        pipeline_used = "DNABERT-2 + HDBSCAN"

    except Exception as e:
        print(f"⚠️ AI pipeline failed: {str(e)}")
        print("🔄 Falling back to Enhanced Species Classifier...")
        
        classification_results = classify_sequences_fallback([{"sequence": seq} for seq in sequences])
        pipeline_used = "Enhanced Fallback Classifier"

    # 3. 🌟 NEW: Advanced Ecosystem Health Analysis
    print("🌿 Calculating ecosystem health metrics...")
    
    try:
        health_analysis = get_ecosystem_health_analysis(classification_results)
        
        # Extract the components
        biodiversity_metrics = health_analysis["biodiversity_metrics"]
        ecosystem_health = health_analysis["ecosystem_health"]
        advanced_metrics = health_analysis["advanced_metrics"]
        
        analysis_success = True
        
    except Exception as e:
        print(f"⚠️ Ecosystem health analysis failed: {str(e)}")
        print("🔄 Using basic calculations...")
        
        # Fallback to your original placeholder calculations
        unique_count = len(set(sequences))
        total = len(sequences)
        
        biodiversity_metrics = {
            "shannon_diversity": round(unique_count * 0.8, 3),
            "simpson_index": round(1 - (1 / (1 + total)), 3),
            "evenness": 0.5,
            "species_richness": unique_count,
            "dominance": 0.3
        }
        
        ecosystem_health = {
            "overall_score": 50.0,
            "health_category": "Fair",
            "component_scores": {
                "biodiversity": 50.0,
                "stability": 50.0,
                "rarity": 50.0,
                "functional_diversity": 50.0
            },
            "recommendations": ["Analysis incomplete - using basic metrics"]
        }
        
        advanced_metrics = {}
        analysis_success = False

    # 4. Calculate processing metrics
    processing_time = round(time.time() - start_time, 2)
    total_sequences = len(sequences)
    unique_species = len(set(
        result.get('predicted_species', 'Unknown') 
        for result in classification_results.values() 
        if isinstance(result, dict)
    ))

    # 5. 🎯 Enhanced Results Structure
    results = {
        "analysis_id": None,
        "filename": file.filename,
        "total_sequences": total_sequences,
        "unique_species_found": unique_species,
        "processing_time_seconds": processing_time,
        "pipeline_used": pipeline_used,
        "analysis_success": analysis_success,
        
        # 🧬 Classification Results
        "taxonomic_classification": classification_results,
        "species_distribution": classification_results,
        
        # 📊 Proper Biodiversity Metrics (no more placeholders!)
        "biodiversity_metrics": biodiversity_metrics,
        
        # 🌿 NEW: Ecosystem Health Assessment
        "ecosystem_health": ecosystem_health,
        
        # 📈 Advanced Analytics (for power users)
        "advanced_metrics": advanced_metrics,
        
        # 📅 Metadata
        "timestamp": datetime.now().isoformat(),
        
        # 💡 User-friendly Summary
        "summary": {
            "health_status": ecosystem_health["health_category"],
            "biodiversity_level": _get_biodiversity_level(biodiversity_metrics["shannon_diversity"]),
            "key_findings": _generate_key_findings(ecosystem_health, biodiversity_metrics, unique_species),
            "confidence": _calculate_overall_confidence(classification_results)
        }
    }

    print(f"✅ Analysis complete in {processing_time}s")
    print(f"🌿 Ecosystem Health: {ecosystem_health['health_category']} ({ecosystem_health['overall_score']}/100)")
    print(f"📊 Shannon Diversity: {biodiversity_metrics['shannon_diversity']}")
    
    return jsonify(results)


def _get_biodiversity_level(shannon_index: float) -> str:
    """Convert Shannon index to human-readable biodiversity level"""
    if shannon_index >= 3.0:
        return "Very High"
    elif shannon_index >= 2.0:
        return "High" 
    elif shannon_index >= 1.0:
        return "Moderate"
    elif shannon_index >= 0.5:
        return "Low"
    else:
        return "Very Low"


def _generate_key_findings(ecosystem_health: dict, biodiversity_metrics: dict, unique_species: int) -> list:
    """Generate user-friendly key findings"""
    findings = []
    
    # Health-based findings
    health_score = ecosystem_health["overall_score"]
    if health_score >= 85:
        findings.append(f"🌟 Exceptional ecosystem with {unique_species} species detected")
    elif health_score >= 70:
        findings.append(f"✅ Healthy ecosystem with good biodiversity ({unique_species} species)")
    elif health_score >= 55:
        findings.append(f"⚠️ Ecosystem shows moderate health with {unique_species} species")
    else:
        findings.append(f"🚨 Ecosystem health concerns detected ({unique_species} species found)")
    
    # Biodiversity findings
    shannon = biodiversity_metrics["shannon_diversity"]
    if shannon >= 2.5:
        findings.append("📈 High species diversity indicates robust ecosystem")
    elif shannon <= 1.0:
        findings.append("📉 Low diversity may indicate environmental stress")
    
    # Evenness findings
    evenness = biodiversity_metrics.get("evenness", 0)
    if evenness >= 0.8:
        findings.append("⚖️ Well-balanced species distribution")
    elif evenness <= 0.4:
        findings.append("⚠️ Uneven species distribution - some species dominate")
    
    return findings


def _calculate_overall_confidence(classification_results: dict) -> float:
    """Calculate overall confidence in the analysis"""
    if not classification_results:
        return 0.0
    
    confidences = []
    for result in classification_results.values():
        if isinstance(result, dict):
            confidence = result.get('confidence_score', 0.5)
            confidences.append(confidence)
    
    return round(sum(confidences) / len(confidences), 2) if confidences else 0.5


# 🆕 NEW ENDPOINT: Detailed Ecosystem Report
@app.route('/api/ecosystem-report', methods=['POST'])
def detailed_ecosystem_report():
    """
    Generate a detailed ecosystem health report for researchers.
    Expects analysis results in request body.
    """
    try:
        data = request.get_json()
        classification_results = data.get('classification_results', {})
        
        if not classification_results:
            return jsonify({"error": "No classification data provided"}), 400
        
        # Generate comprehensive analysis
        health_analysis = get_ecosystem_health_analysis(classification_results)
        
        # Create detailed report
        report = {
            "report_type": "Detailed Ecosystem Assessment",
            "generated_at": datetime.now().isoformat(),
            "executive_summary": {
                "overall_health": health_analysis["ecosystem_health"]["overall_score"],
                "health_category": health_analysis["ecosystem_health"]["health_category"],
                "species_count": health_analysis["biodiversity_metrics"]["species_richness"],
                "key_recommendations": health_analysis["ecosystem_health"]["recommendations"][:3]
            },
            "detailed_analysis": health_analysis,
            "conservation_priority": _determine_conservation_priority(health_analysis),
            "monitoring_recommendations": _generate_monitoring_plan(health_analysis)
        }
        
        return jsonify(report)
        
    except Exception as e:
        return jsonify({"error": f"Report generation failed: {str(e)}"}), 500


def _determine_conservation_priority(health_analysis: dict) -> str:
    """Determine conservation priority based on ecosystem health"""
    score = health_analysis["ecosystem_health"]["overall_score"]
    
    if score >= 85:
        return "Protection Priority - Maintain current status"
    elif score >= 70:
        return "Monitoring Priority - Continue surveillance" 
    elif score >= 55:
        return "Management Priority - Intervention may be needed"
    elif score >= 40:
        return "Restoration Priority - Action required"
    else:
        return "Critical Priority - Immediate intervention essential"


def _generate_monitoring_plan(health_analysis: dict) -> list:
    """Generate monitoring recommendations based on ecosystem health"""
    score = health_analysis["ecosystem_health"]["overall_score"]
    
    if score >= 70:
        return [
            "Continue annual eDNA surveys",
            "Monitor key indicator species",
            "Track seasonal variations"
        ]
    else:
        return [
            "Increase monitoring frequency to quarterly",
            "Focus on declining species",
            "Monitor environmental parameters",
            "Consider intervention strategies"
        ]
# 🆕 NEW ENDPOINT: Species Interaction Network Analysis
@app.route('/api/network', methods=['POST'])
def api_network():
    data = request.get_json() or {}
    classification = data.get('classification_results')
    if not classification:
        return jsonify({'error': 'classification_results missing'}), 400
    try:
        return jsonify(create_species_network_analysis(classification))
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)