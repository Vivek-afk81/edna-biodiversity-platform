import numpy as np
import hdbscan
from .ai_pipeline.embedding_generator import EmbeddingGenerator

class UnsupervisedClassifier:
    """
    Groups sequences into clusters (putative OTUs) based on their
    embedding similarity using an unsupervised clustering algorithm.
    """

    def __init__(self, embedding_generator: EmbeddingGenerator):
        """
        Initializes the classifier with an embedding generator.
        """
        self.embedding_generator = embedding_generator
        # HDBSCAN is a density-based clustering algorithm that finds groups
        # without needing to predefine the number of clusters.
        self.clusterer = hdbscan.HDBSCAN(min_cluster_size=2, min_samples=1)

    def classify_sequences(self, sequences: list):
        """
        Generates embeddings and clusters them to assign a group label to each sequence.

        Args:
            sequences (list of str): A list of DNA sequences.

        Returns:
            dict: A dictionary mapping cluster labels (e.g., 'OTU_1', 'OTU_2')
                  to a list of sequence indices belonging to that cluster.
                  Sequences labeled -1 are considered noise (unclustered).
        """
        if not sequences:
            return {}

        print("🔹 Generating embeddings for classification...")
        embeddings = self.embedding_generator.generate_embeddings(sequences)

        print("🔹 Clustering sequences to discover OTUs...")
        # Fit the clusterer to the embeddings to find groups
        cluster_labels = self.clusterer.fit_predict(embeddings)

        # Organize the results into a dictionary
        results = {}
        for i, label in enumerate(cluster_labels):
            if label == -1:
                # Noise / unclustered sequences
                continue
            
            otu_id = f"OTU_{label + 1}"
            if otu_id not in results:
                results[otu_id] = []
            results[otu_id].append(i)
        
        print(f"✅ Discovered {len(results)} OTUs.")
        return results
