import requests
import time
import io
from Bio import Entrez, SeqIO
from Bio.Blast import NCBIWWW
from backend.app.blast_helper import BlastHelper


class Annotator:
    """
    Annotates DNA clusters or single sequences using BLAST and lineage lookup.
    Can work with clusters (via BlastHelper) or directly with NCBI BLAST.
    """
    def __init__(self, email: str = None):
        """
        Initializes the annotator.
        - If email is provided, uses Biopython + NCBI API.
        - Always sets up BlastHelper for simulated/local annotations.
        """
        if email:
            Entrez.email = email
        self.blast_helper = BlastHelper()

    def annotate_clusters(self, clusters):
        """
        Annotate groups of DNA sequences using BlastHelper.
        """
        print(f"I found {len(clusters)} groups of DNA sequences!")
        print("Now let me figure out what creatures they belong to...")

        annotations = {}

        for cluster_name, sequence_indices in clusters.items():
            print(f"\nLooking at {cluster_name}...")

            # Pick one DNA sequence from each group (the representative)
            representative_sequence = self._pick_best_representative(sequence_indices)

            # Ask our BLAST helper what creature this DNA belongs to
            lineage, confidence = self.blast_helper.identify_sequence(representative_sequence)

            # Save the answer
            annotations[cluster_name] = {
                'lineage': lineage,
                'confidence': confidence,
                'num_sequences': len(sequence_indices),
                'representative': representative_sequence[:50] + '...'
            }

            print(f"  Found: {lineage} (confidence: {confidence:.1f}%)")

        return annotations

    def _pick_best_representative(self, sequence_indices):
        """
        Pick the best DNA sequence from a group.
        For now, just return a placeholder.
        """
        return "ATCGATCGATCGATCGATCG"

    def get_lineage(self, sequence: str):
        """
        Performs a BLAST search via NCBI and retrieves taxonomy for the top hit.
        If BLAST fails, falls back to BlastHelper.
        """
        if not Entrez.email:
            # Fallback if no email was provided → use BlastHelper
            print("No Entrez email provided, falling back to BlastHelper...")
            return self.blast_helper.identify_sequence(sequence)

        print(f"Annotating sequence (first 30 bp): {sequence[:30]}...")
        try:
            # Use qblast to search the nucleotide database
            result_handle = NCBIWWW.qblast(
                program="blastn",
                database="nt",
                sequence=sequence,
                entrez_query="eukaryotes[Organism]"
            )

            blast_result = result_handle.read()
            if "<Hit_accession>" not in blast_result:
                print("No BLAST hit found.")
                return {"title": "No BLAST hit found", "lineage": "Unknown"}

            accession = blast_result.split("<Hit_accession>")[1].split("</Hit_accession>")[0]
            title = blast_result.split("<Hit_def>")[1].split("</Hit_def>")[0]
            print(f"Best hit accession: {accession}")

            # Fetch the GenBank record
            handle = Entrez.efetch(db="nucleotide", id=accession, rettype="gb", retmode="text")
            record = SeqIO.read(handle, "genbank")
            handle.close()

            lineage = record.annotations.get("taxonomy", ["Unknown"])
            print(f"Found lineage: {' -> '.join(lineage)}")

            return {"title": title, "lineage": " -> ".join(lineage)}

        except Exception as e:
            print(f"An error occurred during annotation: {e}")
            return {"title": "Annotation Error", "lineage": str(e)}
