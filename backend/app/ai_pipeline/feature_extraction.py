import torch
import numpy as np
from .deep_learning import eDNAAutoencoder, eDNATrainer, SequenceDataset
from torch.utils.data import DataLoader

class FeatureExtractor:
    """
    Feature extraction using convolutional autoencoder for eDNA sequences.
    """

    def __init__(self, seq_len=500, latent_dim=64, device='cpu'):
        """
        Initializes the feature extractor.

        Args:
            seq_len (int): Maximum sequence length.
            latent_dim (int): Dimension of latent space (features).
            device (str): Device to run the model on ('cpu' or 'cuda').
        """
        self.seq_len = seq_len
        self.latent_dim = latent_dim
        self.device = device if torch.cuda.is_available() and device == 'cuda' else 'cpu'

        # Initialize the autoencoder model
        self.model = eDNAAutoencoder(seq_len=seq_len, latent_dim=latent_dim)
        self.trainer = eDNATrainer(self.model, device=self.device)

    def train_autoencoder(self, sequences, epochs=100, batch_size=16, lr=0.001):
        """
        Trains the autoencoder on the provided sequences.

        Args:
            sequences (list of str): List of DNA sequences for training.
            epochs (int): Number of training epochs.
            batch_size (int): Batch size for training.
            lr (float): Learning rate.

        Returns:
            list: Training losses per epoch.
        """
        losses = self.trainer.train_autoencoder(sequences, epochs=epochs,
                                               batch_size=batch_size, lr=lr)
        return losses

    def extract_features(self, sequences):
        """
        Extracts features from sequences using the trained autoencoder.

        Args:
            sequences (list of str): List of DNA sequences.

        Returns:
            np.ndarray: Array of extracted features.
        """
        if not sequences:
            return np.array([])

        features = self.trainer.extract_features(sequences)
        return features

    def save_model(self, filepath):
        """
        Saves the trained model to a file.

        Args:
            filepath (str): Path to save the model.
        """
        self.trainer.save_model(filepath)

    def load_model(self, filepath):
        """
        Loads a trained model from a file.

        Args:
            filepath (str): Path to the saved model.
        """
        self.trainer.load_model(filepath)

    def get_model_summary(self):
        """
        Returns a summary of the model architecture.

        Returns:
            str: Model summary.
        """
        return str(self.model)
