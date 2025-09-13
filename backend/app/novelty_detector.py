# This helps us find DNA that might belong to completely new, unknown creatures!
import numpy as np
from sklearn.neighbors import NearestNeighbors
import hdbscan

class NoveltyDetector:
    def __init__(self, novelty_threshold=0.85):
        """
        novelty_threshold: How different DNA needs to be to be considered "novel"
        Lower numbers = more strict about calling things "novel"
        """
        self.novelty_threshold = novelty_threshold
        
    def detect_novel_sequences(self, embeddings, cluster_labels, annotations):
        """
        This function is like a detective looking for mysterious DNA that doesn't match anything we know!
        """
        print("🔍 Looking for mysterious, unknown creatures...")
        
        novel_candidates = []
        
        # Look at each cluster
        unique_clusters = set(cluster_labels)
        unique_clusters.discard(-1)  # Remove noise points
        
        for cluster_id in unique_clusters:
            cluster_name = f"OTU_{cluster_id}"
            
            if cluster_name in annotations:
                annotation = annotations[cluster_name]
                confidence = annotation.get('confidence', 0)
                lineage = annotation.get('lineage', 'Unknown')
                
                # Check if this might be something new and exciting!
                is_novel = self._is_potentially_novel(confidence, lineage, cluster_id, embeddings, cluster_labels)
                
                if is_novel:
                    novelty_score = self._calculate_novelty_score(confidence, lineage)
                    
                    novel_candidates.append({
                        'cluster_id': cluster_name,
                        'novelty_score': novelty_score,
                        'reason': self._get_novelty_reason(confidence, lineage),
                        'confidence': confidence,
                        'lineage': lineage,
                        'num_sequences': np.sum(cluster_labels == cluster_id)
                    })
                    
                    print(f"🌟 Found potential new species: {cluster_name}")
                    print(f"   Reason: {self._get_novelty_reason(confidence, lineage)}")
                    print(f"   Novelty Score: {novelty_score:.2f}/1.00")
        
        # Sort by novelty score (most exciting first!)
        novel_candidates.sort(key=lambda x: x['novelty_score'], reverse=True)
        
        if novel_candidates:
            print(f"\n🎉 Found {len(novel_candidates)} potentially new or rare species!")
        else:
            print("\n😌 All sequences match known species pretty well.")
        
        return novel_candidates
    
    def _is_potentially_novel(self, confidence, lineage, cluster_id, embeddings, cluster_labels):
        """Decide if a cluster might represent something novel"""
        
        # Reason 1: Low confidence from BLAST
        if confidence < (self.novelty_threshold * 100):
            return True
        
        # Reason 2: Generic or unknown lineage
        if any(word in lineage.lower() for word in ['unknown', 'unclassified', 'environmental']):
            return True
        
        # Reason 3: The cluster is isolated from others (unique characteristics)
        cluster_embeddings = embeddings[cluster_labels == cluster_id]
        if len(cluster_embeddings) > 0:
            isolation_score = self._calculate_isolation_score(cluster_embeddings, embeddings)
            if isolation_score > 0.7:  # Very isolated cluster
                return True
        
        return False
    
    def _calculate_isolation_score(self, cluster_embeddings, all_embeddings):
        """Calculate how isolated this cluster is from others"""
        if len(cluster_embeddings) == 0:
            return 0
        
        # Find distances to nearest neighbors outside the cluster
        cluster_center = np.mean(cluster_embeddings, axis=0)
        
        # Use k-nearest neighbors to find how far this cluster is from others
        knn = NearestNeighbors(n_neighbors=min(10, len(all_embeddings)))
        knn.fit(all_embeddings)
        
        distances, _ = knn.kneighbors([cluster_center])
        avg_distance = np.mean(distances)
        
        # Convert to a score between 0 and 1
        isolation_score = min(avg_distance / 2.0, 1.0)  # Normalize roughly
        
        return isolation_score
    
    def _calculate_novelty_score(self, confidence, lineage):
        """Calculate how novel this sequence might be (0-1 scale)"""
        novelty_score = 0.0
        
        # Lower confidence = higher novelty
        confidence_score = (100 - confidence) / 100
        novelty_score += confidence_score * 0.6
        
        # Unknown/generic terms = higher novelty
        unknown_words = ['unknown', 'unclassified', 'environmental', 'uncultured']
        unknown_score = sum(1 for word in unknown_words if word in lineage.lower()) / len(unknown_words)
        novelty_score += unknown_score * 0.4
        
        return min(novelty_score, 1.0)
    
    def _get_novelty_reason(self, confidence, lineage):
        """Explain why we think this might be novel"""
        reasons = []
        
        if confidence < 85:
            reasons.append(f"Low similarity to known species ({confidence:.1f}%)")
        
        unknown_words = ['unknown', 'unclassified', 'environmental', 'uncultured']
        if any(word in lineage.lower() for word in unknown_words):
            reasons.append("Matches only generic/unclassified entries")
        
        if not reasons:
            reasons.append("Isolated from other sequences")
        
        return "; ".join(reasons)
