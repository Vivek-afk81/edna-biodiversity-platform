from Bio import Entrez, SeqIO
from Bio.Blast import NCBIWWW
import io

class Annotator:
    """
    Annotates a DNA sequence by finding its closest match in the NCBI database
    and retrieving its full taxonomic lineage.
    """
    def __init__(self, email: str):
        """
        Initializes the annotator. NCBI requires an email address for API access.
        """
        if not email:
            raise ValueError("An email address is required for NCBI API access.")
        Entrez.email = email

    def get_lineage(self, sequence: str):
        """
        Performs a BLAST search and retrieves the taxonomy for the top hit.

        Args:
            sequence (str): The DNA sequence to annotate.

        Returns:
            dict: A dictionary containing the best hit's title and full taxonomic lineage,
                  or an error message if no hit is found.
        """
        print(f"Annotating sequence: {sequence[:30]}...")
        try:
            # Use qblast to search the nucleotide database (nt)
            result_handle = NCBIWWW.qblast(
                program="blastn",
                database="nt",
                sequence=sequence,
                entrez_query="eukaryotes[Organism]" # Limit search to eukaryotes
            )

            # The result is in XML format. We need to find the accession number of the best hit.
            # A more robust parser would be better, but for a simple case, we can find the first accession.
            blast_result = result_handle.read()
            if "<Hit_accession>" not in blast_result:
                print("No BLAST hit found.")
                return {"title": "No BLAST hit found", "lineage": "Unknown"}

            accession = blast_result.split("<Hit_accession>")[1].split("</Hit_accession>")[0]
            title = blast_result.split("<Hit_def>")[1].split("</Hit_def>")[0]
            print(f"Best hit accession: {accession}")

            # Now use the accession to get the full record from NCBI
            handle = Entrez.efetch(db="nucleotide", id=accession, rettype="gb", retmode="text")
            record = SeqIO.read(handle, "genbank")
            handle.close()

            # From the record, get the taxonomy information
            lineage = record.annotations.get("taxonomy", ["Unknown"])
            
            print(f"Found lineage: {' -> '.join(lineage)}")
            return {"title": title, "lineage": " -> ".join(lineage)}

        except Exception as e:
            print(f"An error occurred during annotation: {e}")
            return {"title": "Annotation Error", "lineage": str(e)}