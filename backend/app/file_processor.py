import pyfastx
import os
from typing import List, Dict, Tuple


class FastaProcessor:
    """
    Optimized FASTA file processor for eDNA analysis
    Performance target: Process 1,000 sequences in <5 seconds
    """

    def __init__(self):
        self.supported_formats = ['.fasta', '.fa', '.fas', '.txt']

    def parse_fasta(self, filepath: str) -> List[Dict[str, str]]:
        sequences = []
        try:
            fasta_file = pyfastx.Fasta(filepath)
            for seq_name, sequence in fasta_file.items():
                seq_dict = {
                    'id': seq_name,
                    'description': '',
                    'sequence': sequence,
                    'length': len(sequence),
                    'gc_content': self.calculate_gc_content(sequence),
                    'n_content': sequence.upper().count('N'),
                    'quality_score': self.calculate_quality_score(sequence)
                }
                sequences.append(seq_dict)
        except Exception as e:
            print(f"pyfastx failed, using fallback parser: {e}")
            sequences = self._fallback_parse_fasta(filepath)
        return sequences

    def calculate_gc_content(self, sequence: str) -> float:
        sequence = sequence.upper()
        gc_count = sequence.count('G') + sequence.count('C')
        total_bases = len(sequence.replace('N', ''))
        return round((gc_count / total_bases) * 100, 2) if total_bases else 0.0

    def calculate_quality_score(self, sequence: str) -> float:
        sequence = sequence.upper()
        n_ratio = sequence.count('N') / len(sequence) if len(sequence) > 0 else 1
        quality_score = max(0, 100 - (n_ratio * 100))
        return round(quality_score, 2)

    def get_kmer_profile(self, sequence: str, k: int = 6) -> Dict[str, int]:
        sequence = sequence.upper().replace('N', '')
        kmers = {}
        for i in range(len(sequence) - k + 1):
            kmer = sequence[i:i + k]
            if all(base in 'ATGC' for base in kmer):
                kmers[kmer] = kmers.get(kmer, 0) + 1
        return kmers

    def _fallback_parse_fasta(self, filepath: str) -> List[Dict[str, str]]:
        sequences = []
        current_seq = {'id': '', 'sequence': ''}
        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('>'):
                    if current_seq['id'] and current_seq['sequence']:
                        current_seq['length'] = len(current_seq['sequence'])
                        current_seq['gc_content'] = self.calculate_gc_content(current_seq['sequence'])
                        current_seq['n_content'] = current_seq['sequence'].upper().count('N')
                        current_seq['quality_score'] = self.calculate_quality_score(current_seq['sequence'])
                        current_seq['description'] = ''
                        sequences.append(current_seq.copy())
                    current_seq = {'id': line[1:].split()[0], 'sequence': ''}
                else:
                    current_seq['sequence'] += line
            if current_seq['id'] and current_seq['sequence']:
                current_seq['length'] = len(current_seq['sequence'])
                current_seq['gc_content'] = self.calculate_gc_content(current_seq['sequence'])
                current_seq['n_content'] = current_seq['sequence'].upper().count('N')
                current_seq['quality_score'] = self.calculate_quality_score(current_seq['sequence'])
                current_seq['description'] = ''
                sequences.append(current_seq)
        return sequences

    def validate_fasta(self, filepath: str) -> Tuple[bool, str]:
        if not os.path.exists(filepath):
            return False, "File does not exist"
        if os.path.getsize(filepath) == 0:
            return False, "File is empty"
        try:
            with open(filepath, 'r') as file:
                lines = [file.readline() for _ in range(10)]
            if not any(line.startswith('>') for line in lines):
                return False, "No FASTA headers found (lines starting with '>')"
            return True, "Valid FASTA file"
        except Exception as e:
            return False, f"File validation error: {str(e)}"
