# This file helps us ask the internet "what creature is this DNA from?"
import requests
import time
import xml.etree.ElementTree as ET
from models import BlastCache, get_database

class BlastHelper:
    def __init__(self):
        self.session, self.engine = get_database()
        
    def identify_sequence(self, dna_sequence):
        """
        This function is like asking a teacher: "What animal does this DNA belong to?"
        """
        # First, check if we already know the answer (like looking in our notebook)
        cached_result = self.session.query(BlastCache).filter_by(sequence=dna_sequence).first()
        
        if cached_result:
            print(f"I already know this one! It's: {cached_result.lineage}")
            return cached_result.lineage, cached_result.confidence
        
        # If we don't know, ask the internet
        print("I don't know this one, let me ask the internet...")
        lineage, confidence = self._ask_ncbi_blast(dna_sequence)
        
        # Remember the answer for next time (like writing it in our notebook)
        self._save_to_cache(dna_sequence, lineage, confidence)
        
        return lineage, confidence
    
    def _ask_ncbi_blast(self, sequence):
        """
        This actually talks to NCBI (a big database on the internet)
        """
        try:
            # Step 1: Send our DNA sequence to NCBI
            submit_params = {
                'CMD': 'Put',
                'PROGRAM': 'blastn',
                'DATABASE': 'nt',
                'QUERY': sequence,
                'FORMAT_TYPE': 'XML'
            }
            
            response = requests.post('https://blast.ncbi.nlm.nih.gov/Blast.cgi', data=submit_params)
            
            # Step 2: Get a ticket number (Request ID)
            request_id = self._extract_request_id(response.text)
            if not request_id:
                return "Unknown", 0.0
            
            # Step 3: Wait a bit (NCBI needs time to think)
            print("Waiting for NCBI to finish thinking...")
            time.sleep(10)
            
            # Step 4: Get the results
            result_params = {
                'CMD': 'Get',
                'RID': request_id,
                'FORMAT_TYPE': 'XML'
            }
            
            result_response = requests.get('https://blast.ncbi.nlm.nih.gov/Blast.cgi', params=result_params)
            
            # Step 5: Read the answer
            lineage, confidence = self._parse_blast_xml(result_response.text)
            
            return lineage, confidence
            
        except Exception as e:
            print(f"Oops, something went wrong: {e}")
            return "Unknown", 0.0
    
    def _extract_request_id(self, response_text):
        """Extract the ticket number from NCBI's response"""
        for line in response_text.splitlines():
            if 'RID =' in line:
                return line.split('=')[1].strip()
        return None
    
    def _parse_blast_xml(self, xml_text):
        """Read NCBI's answer and understand what it means"""
        try:
            root = ET.fromstring(xml_text)
            
            # Look for the best match
            hit = root.find('.//Hit')
            if hit is None:
                return "Unknown", 0.0
            
            # Get the creature's name
            description = hit.find('Hit_def').text
            
            # Get how confident we are
            identity = float(root.find('.//Hsp_identity').text)
            align_length = float(root.find('.//Hsp_align-len').text)
            confidence = (identity / align_length) * 100
            
            # Create a simple lineage (family tree)
            lineage = self._create_simple_lineage(description)
            
            return lineage, confidence
            
        except Exception as e:
            print(f"Couldn't understand NCBI's answer: {e}")
            return "Unknown", 0.0
    
    def _create_simple_lineage(self, description):
        """Turn the creature's name into a simple family tree"""
        # This is a simple version - in real life, you'd want more sophisticated parsing
        if any(word in description.lower() for word in ['fish', 'salmon', 'tuna']):
            return "Eukaryota;Animalia;Chordata;Actinopterygii;Fish"
        elif any(word in description.lower() for word in ['human', 'mouse', 'mammal']):
            return "Eukaryota;Animalia;Chordata;Mammalia;Mammal"
        elif any(word in description.lower() for word in ['bacteria', 'bacterium']):
            return "Bacteria;Unknown_Family"
        else:
            return f"Eukaryota;Unknown_Family;{description.split()[0]}"
    
    def _save_to_cache(self, sequence, lineage, confidence):
        """Save the answer to our notebook so we remember it"""
        cache_entry = BlastCache(
            sequence=sequence,
            lineage=lineage,
            confidence=confidence
        )
        self.session.add(cache_entry)
        self.session.commit()
        print(f"Saved to memory: {lineage}")
