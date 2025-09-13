import hdbscan
import numpy as np

class HDBSCANClusterer:
    """
    Clusters embeddings using HDBSCAN algorithm to discover OTUs.
    """

    def __init__(self, min_cluster_size=2, min_samples=1):
        """
        Initializes the HDBSCAN clusterer.
        """
        self.clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples)

    def cluster_embeddings(self, embeddings):
        """
        Clusters the embeddings and returns OTU clusters.

        Args:
            embeddings (np.ndarray): Array of embeddings.

        Returns:
            dict: Dictionary mapping cluster labels to lists of indices.
        """
        if not isinstance(embeddings, np.ndarray):
            embeddings = np.array(embeddings)

        if embeddings.size == 0:
            return {}

        # Fit the clusterer to the embeddings
        cluster_labels = self.clusterer.fit_predict(embeddings)

        # Organize results
        results = {}
        for i, label in enumerate(cluster_labels):
            if label == -1:
                # Noise / unclustered
                continue
            otu_id = f"OTU_{label + 1}"
            if otu_id not in results:
                results[otu_id] = []
            results[otu_id].append(i)

        return results
