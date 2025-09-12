import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
import os
from sklearn.model_selection import train_test_split

class SequenceDataset(Dataset):
    """Dataset for eDNA sequences"""
    
    def __init__(self, sequences, labels=None, max_len=500):
        self.sequences = sequences
        self.labels = labels
        self.max_len = max_len
        
        # Mapping for nucleotides
        self.nucleotide_to_idx = {'A': 0, 'T': 1, 'G': 2, 'C': 3, 'N': 4}
        
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        seq = self.sequences[idx]
        encoded = self.encode_sequence(seq)
        
        if self.labels is not None:
            return torch.FloatTensor(encoded), self.labels[idx]
        return torch.FloatTensor(encoded)
    
    def encode_sequence(self, seq):
        """One-hot encode DNA sequence"""
        seq = seq.upper()[:self.max_len]
        
        # Pad sequence to max_len
        if len(seq) < self.max_len:
            seq += 'N' * (self.max_len - len(seq))
        
        # One-hot encoding
        encoded = np.zeros((5, self.max_len))  # 5 for A,T,G,C,N
        
        for i, nucleotide in enumerate(seq):
            if nucleotide in self.nucleotide_to_idx:
                encoded[self.nucleotide_to_idx[nucleotide], i] = 1
            else:
                encoded[4, i] = 1  # Unknown nucleotide as N
                
        return encoded

class eDNAAutoencoder(nn.Module):
    """Convolutional Autoencoder for eDNA feature learning"""
    
    def __init__(self, seq_len=500, latent_dim=64):
        super(eDNAAutoencoder, self).__init__()
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Conv1d(5, 32, kernel_size=7, padding=3),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(32)
        )
        
        self.encoder_fc = nn.Linear(128 * 32, latent_dim)
        
        # Decoder
        self.decoder_fc = nn.Linear(latent_dim, 128 * 32)
        
        self.decoder = nn.Sequential(
            nn.ConvTranspose1d(128, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.ConvTranspose1d(64, 32, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.ConvTranspose1d(32, 5, kernel_size=7, padding=3),
            nn.Sigmoid()
        )
        
    def encode(self, x):
        x = self.encoder(x)
        x = x.view(x.size(0), -1)
        return self.encoder_fc(x)
    
    def decode(self, z):
        x = self.decoder_fc(z)
        x = x.view(x.size(0), 128, 32)
        x = self.decoder(x)
        
        # Interpolate to original sequence length
        x = F.interpolate(x, size=500, mode='linear', align_corners=False)
        return x
    
    def forward(self, x):
        z = self.encode(x)
        return self.decode(z), z

class eDNATrainer:
    """Training utilities for eDNA models"""
    
    def __init__(self, model, device='cpu'):
        self.model = model.to(device)
        self.device = device
        
    def train_autoencoder(self, sequences, epochs=100, batch_size=16, lr=0.001):
        """Train the autoencoder"""
        dataset = SequenceDataset(sequences)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()
        
        self.model.train()
        losses = []
        
        print("Starting autoencoder training...")
        
        for epoch in range(epochs):
            epoch_loss = 0
            batch_count = 0
            
            for batch in dataloader:
                batch = batch.to(self.device)
                
                optimizer.zero_grad()
                reconstructed, _ = self.model(batch)
                
                loss = criterion(reconstructed, batch)
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                batch_count += 1
            
            avg_loss = epoch_loss / batch_count
            losses.append(avg_loss)
            
            if epoch % 20 == 0:
                print(f"Epoch {epoch}/{epochs}, Loss: {avg_loss:.6f}")
        
        print("Training completed!")
        return losses
    
    def extract_features(self, sequences):
        """Extract features using trained autoencoder"""
        dataset = SequenceDataset(sequences)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=False)
        
        self.model.eval()
        features = []
        
        with torch.no_grad():
            for batch in dataloader:
                batch = batch.to(self.device)
                _, encoded = self.model(batch)
                features.append(encoded.cpu().numpy())
        
        return np.vstack(features)
    
    def save_model(self, filepath):
        """Save trained model"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        torch.save(self.model.state_dict(), filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load trained model"""
        self.model.load_state_dict(torch.load(filepath, map_location=self.device))
        self.model.eval()
        print(f"Model loaded from {filepath}")
