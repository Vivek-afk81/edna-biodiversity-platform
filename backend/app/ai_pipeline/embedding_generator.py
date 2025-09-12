import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np

class EmbeddingGenerator:
    """
    Uses a pre-trained DNA language model to convert DNA sequences
    into numerical vectors (embeddings).
    """
    def __init__(self, model_name="zhihan1996/DNABERT-2-117M"):
        """
        Initializes the tokenizer and model. This might take a moment
        the first time as it downloads the model from the internet.
        """
        print(f"Loading model {model_name} for embedding generation...")
        # The tokenizer breaks DNA into "words" (k-mers)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        # The model is the "brain" that understands the words
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        # Use a GPU if available, otherwise use the CPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        print(f"Embedding model loaded successfully on {self.device}.")

    def generate_embeddings(self, sequences):
        """
        Takes a list of DNA sequences and returns their embeddings.

        Args:
            sequences (list of str): A list of DNA sequences.

        Returns:
            np.ndarray: A numpy array of embeddings, where each row is an
                        embedding for a sequence.
        """
        if not sequences:
            return np.array()

        # Tokenize the sequences and move them to the GPU/CPU
        inputs = self.tokenizer(sequences, return_tensors='pt', padding=True, truncation=True)["input_ids"]
        inputs = inputs.to(self.device)

        # Tell the model not to calculate gradients, which makes it faster
        with torch.no_grad():
            # Get the model's output
            outputs = self.model(inputs)

        # We use the embedding of the "" token, which represents the whole sequence
        embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        return embeddings