# backend/biodiversity.py

import math
import numpy as np
from collections import Counter

# Optional phylogenetic tools
try:
    from Bio import Phylo, AlignIO, SeqIO
    from Bio.Phylo.TreeConstruction import DistanceCalculator
    import skbio
    import subprocess
    import tempfile
    import os
    HAS_PHYLO = True
except ImportError:
    HAS_PHYLO = False


class BiodiversityCalculator:
    """
    Calculates biodiversity indices (Shannon, Simpson, Evenness, etc.)
    and optionally Faith’s Phylogenetic Diversity (PD) if phylogenetic
    tools are available.
    """

    def __init__(self, counts):
        """
        Args:
            counts (dict): Mapping of {taxon: count}.
        """
        self.counts = counts
        self.total = sum(counts.values())

    # ------------------------
    # Classical diversity indices
    # ------------------------
    def shannon_index(self):
        if self.total == 0:
            return 0
        proportions = [n / self.total for n in self.counts.values() if n > 0]
        return -sum(p * math.log(p) for p in proportions)

    def simpson_index(self):
        if self.total == 0:
            return 0
        proportions = [n / self.total for n in self.counts.values()]
        return 1 - sum(p ** 2 for p in proportions)

    def evenness(self):
        s = len(self.counts)
        if s <= 1:
            return 0
        return self.shannon_index() / math.log(s)

    def richness(self):
        return len([n for n in self.counts.values() if n > 0])

    def dominance(self):
        if self.total == 0:
            return 0
        proportions = [n / self.total for n in self.counts.values()]
        return max(proportions)

    def margalef_index(self):
        s = self.richness()
        if self.total <= 1:
            return 0
        return (s - 1) / math.log(self.total)

    # ------------------------
    # Phylogenetic Diversity (optional)
    # ------------------------
    def phylogenetic_diversity(self, fasta_file):
        """
        Compute Faith’s PD from sequences in a FASTA file.

        Args:
            fasta_file (str): Path to input FASTA file with DNA sequences.

        Returns:
            float: Sum of branch lengths (Faith’s PD), or None if unavailable.
        """
        if not HAS_PHYLO:
            print("⚠️ Biopython / scikit-bio not installed, skipping PD.")
            return None

        # Check if external tools are installed
        if not self._is_tool("mafft") or not self._is_tool("phyml"):
            print("⚠️ MAFFT/PhyML not installed, skipping PD.")
            return None

        with tempfile.TemporaryDirectory() as tmpdir:
            aligned = os.path.join(tmpdir, "aligned.fasta")
            treefile = os.path.join(tmpdir, "tree.newick")

            # Run MAFFT alignment
            subprocess.run(["mafft", "--auto", fasta_file], stdout=open(aligned, "w"), check=True)

            # Run PhyML to build tree
            subprocess.run(["phyml", "-i", aligned, "-d", "nt"], check=True)

            # PhyML outputs as aligned_phyml_tree.txt
            generated_tree = aligned + "_phyml_tree.txt"
            if not os.path.exists(generated_tree):
                return None

            # Parse tree and sum branch lengths
            tree = Phylo.read(generated_tree, "newick")
            return sum(branch.length for branch in tree.get_terminals() + tree.get_nonterminals() if branch.length)

    @staticmethod
    def _is_tool(name):
        """Check if a tool exists in PATH."""
        from shutil import which
        return which(name) is not None

    # ------------------------
    # Reporting
    # ------------------------
    def summary(self, fasta_file=None):
        """
        Return biodiversity metrics summary.

        Args:
            fasta_file (str, optional): Path to FASTA file for PD.
        """
        report = {
            "Total Sequences": self.total,
            "Richness (S)": self.richness(),
            "Shannon Index (H')": round(self.shannon_index(), 4),
            "Simpson Index (1-D)": round(self.simpson_index(), 4),
            "Evenness (J')": round(self.evenness(), 4),
            "Dominance (D)": round(self.dominance(), 4),
            "Margalef Index": round(self.margalef_index(), 4),
        }

        if fasta_file:
            pd = self.phylogenetic_diversity(fasta_file)
            report["Faith’s PD"] = round(pd, 4) if pd else "Not available"

        return report
