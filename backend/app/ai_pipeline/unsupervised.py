import numpy as np
from .embedding_generator import EmbeddingGenerator
from ..clustering import HDBSCANClusterer

class UnsupervisedLearningPipeline:
    """
    Pipeline for unsupervised learning on eDNA sequences.
    Generates embeddings from sequences and clusters them to discover OTUs.
    """

    def __init__(self, embedding_model_name="zhihan1996/DNABERT-2-117M",
                 min_cluster_size=2, min_samples=1):
        """
        Initializes the unsupervised learning pipeline.

        Args:
            embedding_model_name (str): Name of the pre-trained model for embeddings.
            min_cluster_size (int): Minimum cluster size for HDBSCAN.
            min_samples (int): Minimum samples for HDBSCAN.
        """
        self.embedding_generator = EmbeddingGenerator(model_name=embedding_model_name)
        self.clusterer = HDBSCANClusterer(min_cluster_size=min_cluster_size, min_samples=min_samples)

    def generate_embeddings(self, sequences):
        """
        Generates embeddings for a list of DNA sequences.

        Args:
            sequences (list of str): List of DNA sequences.

        Returns:
            np.ndarray: Array of embeddings.
        """
        if not sequences:
            return np.array([])

        embeddings = self.embedding_generator.generate_embeddings(sequences)
        return embeddings

    def cluster_sequences(self, sequences):
        """
        Performs unsupervised clustering on sequences to discover OTUs.

        Args:
            sequences (list of str): List of DNA sequences.

        Returns:
            dict: Dictionary mapping OTU IDs to lists of sequence indices.
        """
        if not sequences:
            return {}

        # Generate embeddings
        embeddings = self.generate_embeddings(sequences)

        # Cluster embeddings
        clusters = self.clusterer.cluster_embeddings(embeddings)

        return clusters

    def run_pipeline(self, sequences):
        """
        Runs the full unsupervised learning pipeline: embedding generation and clustering.

        Args:
            sequences (list of str): List of DNA sequences.

        Returns:
            dict: Results containing embeddings and clusters.
                - 'embeddings': np.ndarray of embeddings
                - 'clusters': dict of OTU clusters
        """
        embeddings = self.generate_embeddings(sequences)
        clusters = self.clusterer.cluster_embeddings(embeddings) if embeddings.size > 0 else {}

        results = {
            'embeddings': embeddings,
            'clusters': clusters
        }

        return results
