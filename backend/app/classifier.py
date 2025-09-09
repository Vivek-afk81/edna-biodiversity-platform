"""
Mock Species Classifier for eDNA Biodiversity Analysis
Simulates AI-powered taxonomic classification with 85-90% accuracy
Based on GC content patterns and k-mer profiles as specified
"""

import numpy as np
import random
from typing import List, Dict, Any
from collections import Counter

class MockSpeciesClassifier:
    """
    Mock classifier that simulates deep learning-based taxonomic identification
    Designed to achieve 85-90% simulated accuracy for demo purposes
    """

    def __init__(self):
        # Marine taxonomy database (simplified for MVP)
        self.marine_taxa = {
            'high_gc': [
                'Prochlorococcus_marinus',
                'Synechococcus_sp',
                'Pelagibacter_ubique',
                'Alteromonas_macleodii',
                'Vibrio_alginolyticus'
            ],
            'medium_gc': [
                'Pseudoalteromonas_haloplanktis',
                'Marinobacter_hydrocarbonoclasticus',
                'Rhodobacteraceae_sp',
                'Flavobacteria_sp',
                'Gammaproteobacteria_sp'
            ],
            'low_gc': [
                'Candidatus_Carsonella',
                'Bacteroidetes_sp',
                'Planctomycetes_sp',
                'Verrucomicrobia_sp',
                'Actinobacteria_sp'
            ],
            'novel_taxa': [
                'Unknown_Deep_Sea_Taxon_A',
                'Unknown_Deep_Sea_Taxon_B',
                'Novel_Marine_Eukaryote_C',
                'Unclassified_Protist_D',
                'Deep_Ocean_Mystery_E'
            ]
        }

        # Confidence thresholds for classification
        self.confidence_thresholds = {
            'high': 0.85,
            'medium': 0.70,
            'low': 0.50
        }

        # Ecological roles mapping
        self.ecological_roles = {
            'primary_producer': 'Primary Producer (Photosynthesis)',
            'decomposer': 'Decomposer (Organic Matter Breakdown)',
            'symbiont': 'Symbiont (Host Association)',
            'pathogen': 'Potential Pathogen',
            'biogeochemical': 'Biogeochemical Cycling',
            'unknown': 'Unknown Ecological Role'
        }

    def classify_sequences(self, sequences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform mock taxonomic classification on sequences

        Args:
            sequences: List of sequence dictionaries from FASTA processor

        Returns:
            Dictionary containing classification results and metadata
        """
        classified_sequences = []
        species_counts = Counter()
        novel_species_count = 0
        total_confidence = 0

        for seq in sequences:
            # Perform classification based on GC content and length
            classification = self._classify_single_sequence(seq)
            classified_sequences.append(classification)

            species_counts[classification['predicted_taxon']] += 1
            total_confidence += classification['confidence']

            if 'Novel' in classification['predicted_taxon'] or 'Unknown' in classification['predicted_taxon']:
                novel_species_count += 1

        # Calculate summary statistics
        average_confidence = round(total_confidence / len(sequences), 2) if sequences else 0
        novel_species_ratio = round((novel_species_count / len(sequences)) * 100, 2) if sequences else 0

        return {
            'total_sequences': len(sequences),
            'classified_sequences': classified_sequences,
            'species_distribution': dict(species_counts.most_common()),
            'unique_taxa_identified': len(species_counts),
            'novel_species_discovered': novel_species_count,
            'novel_species_ratio_percent': novel_species_ratio,
            'average_confidence': average_confidence,
            'classification_summary': self._generate_classification_summary(species_counts)
        }

    def _classify_single_sequence(self, sequence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a single sequence based on its characteristics"""

        gc_content = sequence_data.get('gc_content', 50)
        length = sequence_data.get('length', 0)
        quality_score = sequence_data.get('quality_score', 50)

        # Determine taxonomic group based on GC content
        if gc_content >= 65:
            taxa_group = 'high_gc'
        elif gc_content >= 40:
            taxa_group = 'medium_gc'
        else:
            taxa_group = 'low_gc'

        # Add some randomness for novel species discovery (10-15% chance)
        if random.random() < 0.12:  # 12% chance of novel species
            taxa_group = 'novel_taxa'

        # Select species from appropriate group
        predicted_species = random.choice(self.marine_taxa[taxa_group])

        # Calculate confidence based on multiple factors
        base_confidence = self._calculate_confidence(gc_content, length, quality_score)

        # Assign ecological role
        ecological_role = self._assign_ecological_role(predicted_species, gc_content)

        return {
            'sequence_id': sequence_data.get('id', 'unknown'),
            'predicted_taxon': predicted_species,
            'confidence': base_confidence,
            'taxonomic_rank': self._get_taxonomic_rank(predicted_species),
            'ecological_role': ecological_role,
            'gc_content': gc_content,
            'sequence_length': length,
            'quality_score': quality_score,
            'classification_method': 'Mock_AI_Classifier_v1.0'
        }

    def _calculate_confidence(self, gc_content: float, length: int, quality_score: float) -> float:
        """Calculate classification confidence based on sequence characteristics"""

        # Base confidence starts at 70%
        confidence = 0.70

        # Adjust based on sequence length (optimal range: 200-800bp)
        if 200 <= length <= 800:
            confidence += 0.15
        elif 100 <= length < 200 or 800 < length <= 1200:
            confidence += 0.05
        else:
            confidence -= 0.10

        # Adjust based on quality score
        if quality_score >= 90:
            confidence += 0.10
        elif quality_score >= 75:
            confidence += 0.05
        else:
            confidence -= 0.05

        # Add random variation to simulate real classifier uncertainty
        confidence += random.uniform(-0.05, 0.05)

        # Ensure confidence is within valid range
        confidence = max(0.45, min(0.95, confidence))

        return round(confidence, 3)

    def _get_taxonomic_rank(self, species_name: str) -> str:
        """Determine taxonomic rank based on species name"""
        if 'Unknown' in species_name or 'Novel' in species_name or 'Mystery' in species_name:
            return 'Novel/Unclassified'
        elif '_sp' in species_name:
            return 'Genus'
        else:
            return 'Species'

    def _assign_ecological_role(self, species_name: str, gc_content: float) -> str:
        """Assign ecological role based on species and characteristics"""

        # Rule-based ecological role assignment
        if 'Prochlorococcus' in species_name or 'Synechococcus' in species_name:
            return self.ecological_roles['primary_producer']
        elif 'Pelagibacter' in species_name:
            return self.ecological_roles['biogeochemical']
        elif 'Vibrio' in species_name:
            return self.ecological_roles['pathogen']
        elif 'Bacteroidetes' in species_name or 'Flavobacteria' in species_name:
            return self.ecological_roles['decomposer']
        elif 'Candidatus' in species_name:
            return self.ecological_roles['symbiont']
        elif 'Unknown' in species_name or 'Novel' in species_name:
            return self.ecological_roles['unknown']
        else:
            # Default assignment based on GC content
            if gc_content > 60:
                return self.ecological_roles['primary_producer']
            else:
                return self.ecological_roles['biogeochemical']

    def _generate_classification_summary(self, species_counts: Counter) -> List[Dict[str, Any]]:
        """Generate summary of top classified species"""

        summary = []
        total_sequences = sum(species_counts.values())

        for species, count in species_counts.most_common(10):  # Top 10 species
            percentage = round((count / total_sequences) * 100, 2)
            summary.append({
                'species': species,
                'count': count,
                'percentage': percentage,
                'rank': len(summary) + 1
            })

        return summary
