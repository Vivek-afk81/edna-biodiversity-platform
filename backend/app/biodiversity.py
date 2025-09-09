"""
Biodiversity Metrics Calculator
Implements Shannon and Simpson indices plus additional marine-specific metrics
Based on standard ecological formulas for eDNA analysis
"""

import math
import numpy as np
from typing import Dict, List, Any, Tuple
from collections import Counter
from datetime import datetime

class BiodiversityCalculator:
    """
    Calculate comprehensive biodiversity metrics for marine eDNA samples
    Implements standard ecological indices with marine-specific adaptations
    """
    
    def __init__(self):
        self.indices = {
            'shannon': 'Shannon Diversity Index (H)',
            'simpson': 'Simpson Diversity Index (D)',
            'evenness': 'Shannon Evenness Index (J)',
            'richness': 'Species Richness (S)',
            'dominance': 'Dominance Index',
            'margalef': 'Margalef Richness Index'
        }
    
    def calculate_metrics(self, classification_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive biodiversity metrics from classification results
        
        Args:
            classification_results: Output from species classifier
            
        Returns:
            Dictionary containing all biodiversity metrics and interpretations
        """
        
        species_counts = classification_results.get('species_distribution', {})
        total_sequences = classification_results.get('total_sequences', 0)
        
        if not species_counts or total_sequences == 0:
            return self._empty_metrics()
        
        # Calculate core biodiversity indices
        shannon_index = self._calculate_shannon_index(species_counts, total_sequences)
        simpson_index = self._calculate_simpson_index(species_counts, total_sequences)
        evenness_index = self._calculate_evenness_index(shannon_index, len(species_counts))
        richness = len(species_counts)
        dominance_index = self._calculate_dominance_index(species_counts, total_sequences)
        margalef_index = self._calculate_margalef_index(richness, total_sequences)
        
        # Calculate marine-specific metrics
        novel_species_ratio = classification_results.get('novel_species_ratio_percent', 0)
        rare_species_count = self._count_rare_species(species_counts, total_sequences)
        dominant_species = max(species_counts.items(), key=lambda x: x[1])
        
        # Generate interpretations
        shannon_interpretation = self._interpret_shannon(shannon_index)
        simpson_interpretation = self._interpret_simpson(simpson_index)
        overall_diversity = self._assess_overall_diversity(shannon_index, simpson_index, evenness_index)
        
        return {
            'indices': {
                'shannon_diversity': round(shannon_index, 4),
                'simpson_diversity': round(simpson_index, 4),
                'shannon_evenness': round(evenness_index, 4),
                'species_richness': richness,
                'dominance_index': round(dominance_index, 4),
                'margalef_richness': round(margalef_index, 4)
            },
            'marine_metrics': {
                'novel_species_discovered': classification_results.get('novel_species_discovered', 0),
                'novel_species_ratio_percent': novel_species_ratio,
                'rare_species_count': rare_species_count,
                'dominant_species': dominant_species[0],
                'dominant_species_percentage': round((dominant_species[1] / total_sequences) * 100, 2)
            },
            'interpretations': {
                'shannon_interpretation': shannon_interpretation,
                'simpson_interpretation': simpson_interpretation,
                'overall_diversity_assessment': overall_diversity,
                'ecosystem_health': self._assess_ecosystem_health(shannon_index, novel_species_ratio)
            },
            'metadata': {
                'total_sequences_analyzed': total_sequences,
                'unique_taxa_identified': richness,
                'calculation_timestamp': self._get_timestamp(),
                'methodology': 'Standard ecological indices with marine adaptations'
            }
        }
    
    def _calculate_shannon_index(self, species_counts: Dict[str, int], total: int) -> float:
        """
        Calculate Shannon Diversity Index (H)
        H = -Σ(pi * ln(pi)) where pi is the proportion of species i
        """
        shannon = 0
        for count in species_counts.values():
            if count > 0:
                proportion = count / total
                shannon -= proportion * math.log(proportion)
        return shannon
    
    def _calculate_simpson_index(self, species_counts: Dict[str, int], total: int) -> float:
        """
        Calculate Simpson Diversity Index (D)
        D = Σ(pi^2) where pi is the proportion of species i
        """
        simpson = 0
        for count in species_counts.values():
            if count > 0:
                proportion = count / total
                simpson += proportion ** 2
        return simpson
    
    def _calculate_evenness_index(self, shannon: float, richness: int) -> float:
        """
        Calculate Shannon Evenness Index (J)
        J = H / ln(S) where H is Shannon index and S is species richness
        """
        if richness <= 1:
            return 0
        return shannon / math.log(richness)
    
    def _calculate_dominance_index(self, species_counts: Dict[str, int], total: int) -> float:
        """Calculate dominance index (1 - Simpson)"""
        simpson = self._calculate_simpson_index(species_counts, total)
        return 1 - simpson
    
    def _calculate_margalef_index(self, richness: int, total: int) -> float:
        """
        Calculate Margalef Richness Index
        DMg = (S - 1) / ln(N) where S is richness and N is total individuals
        """
        if total <= 1:
            return 0
        return (richness - 1) / math.log(total)
    
    def _count_rare_species(self, species_counts: Dict[str, int], total: int, threshold: float = 0.01) -> int:
        """Count species representing less than threshold % of total"""
        rare_count = 0
        for count in species_counts.values():
            if (count / total) < threshold:
                rare_count += 1
        return rare_count
    
    def _interpret_shannon(self, shannon: float) -> str:
        """Interpret Shannon index value"""
        if shannon < 1.0:
            return "Low diversity - ecosystem may be stressed or highly specialized"
        elif shannon < 2.0:
            return "Moderate diversity - typical of many marine environments"
        elif shannon < 3.0:
            return "High diversity - healthy and complex marine ecosystem"
        else:
            return "Very high diversity - exceptionally rich marine environment"
    
    def _interpret_simpson(self, simpson: float) -> str:
        """Interpret Simpson index value"""
        if simpson > 0.7:
            return "Low diversity - dominated by few species"
        elif simpson > 0.5:
            return "Moderate diversity - some species dominance"
        elif simpson > 0.3:
            return "High diversity - well-distributed species abundance"
        else:
            return "Very high diversity - no clear dominant species"
    
    def _assess_overall_diversity(self, shannon: float, simpson: float, evenness: float) -> str:
        """Provide overall diversity assessment"""
        
        # Scoring system (0-10)
        shannon_score = min(10, shannon * 3)  # Shannon typically 0-3+
        simpson_score = (1 - simpson) * 10    # Convert to diversity score
        evenness_score = evenness * 10        # Evenness 0-1
        
        overall_score = (shannon_score + simpson_score + evenness_score) / 3
        
        if overall_score >= 8:
            return "Excellent biodiversity - very healthy marine ecosystem"
        elif overall_score >= 6:
            return "Good biodiversity - stable marine community"
        elif overall_score >= 4:
            return "Moderate biodiversity - ecosystem under some stress"
        else:
            return "Poor biodiversity - ecosystem may be degraded or highly disturbed"
    
    def _assess_ecosystem_health(self, shannon: float, novel_ratio: float) -> str:
        """Assess ecosystem health based on diversity and novel species"""
        
        health_score = 0
        
        # Shannon contribution
        if shannon >= 2.5:
            health_score += 3
        elif shannon >= 1.5:
            health_score += 2
        else:
            health_score += 1
        
        # Novel species contribution
        if 5 <= novel_ratio <= 15:  # Optimal novel species range
            health_score += 2
        elif novel_ratio < 5 or novel_ratio > 20:
            health_score += 1
        
        if health_score >= 4:
            return "Healthy ecosystem with good balance of known and novel species"
        elif health_score >= 3:
            return "Moderately healthy ecosystem"
        else:
            return "Ecosystem health concerns - low diversity or unusual species composition"
    
    def calculate_rarefaction_curve(self, species_counts: Dict[str, int], max_samples: int = None) -> Dict[str, List]:
        """
        Calculate rarefaction curve for species accumulation analysis
        """
        if not max_samples:
            max_samples = sum(species_counts.values())
        
        # Create individual occurrence list
        individuals = []
        for species, count in species_counts.items():
            individuals.extend([species] * count)
        
        # Shuffle for randomization
        import random
        random.shuffle(individuals)
        
        # Calculate accumulation curve
        sample_sizes = []
        species_counts_curve = []
        observed_species = set()
        
        step_size = max(1, max_samples // 50)  # 50 points on curve
        
        for i in range(step_size, max_samples + 1, step_size):
            sample = individuals[:i]
            observed_species.update(sample)
            
            sample_sizes.append(i)
            species_counts_curve.append(len(observed_species))
        
        return {
            'sample_sizes': sample_sizes,
            'species_counts': species_counts_curve,
            'expected_total_species': len(species_counts)
        }
    
    def calculate_beta_diversity(self, sample1_counts: Dict[str, int], sample2_counts: Dict[str, int]) -> Dict[str, float]:
        """
        Calculate beta diversity metrics between two samples
        """
        # Get all species from both samples
        all_species = set(sample1_counts.keys()) | set(sample2_counts.keys())
        
        # Calculate shared species
        shared_species = set(sample1_counts.keys()) & set(sample2_counts.keys())
        
        # Calculate Jaccard similarity
        jaccard_similarity = len(shared_species) / len(all_species) if all_species else 0
        
        # Calculate Bray-Curtis dissimilarity
        numerator = 0
        denominator = 0
        
        for species in all_species:
            count1 = sample1_counts.get(species, 0)
            count2 = sample2_counts.get(species, 0)
            
            numerator += abs(count1 - count2)
            denominator += count1 + count2
        
        bray_curtis_dissimilarity = numerator / denominator if denominator > 0 else 0
        bray_curtis_similarity = 1 - bray_curtis_dissimilarity
        
        return {
            'jaccard_similarity': round(jaccard_similarity, 4),
            'bray_curtis_similarity': round(bray_curtis_similarity, 4),
            'bray_curtis_dissimilarity': round(bray_curtis_dissimilarity, 4),
            'shared_species': len(shared_species),
            'unique_to_sample1': len(set(sample1_counts.keys()) - set(sample2_counts.keys())),
            'unique_to_sample2': len(set(sample2_counts.keys()) - set(sample1_counts.keys()))
        }
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure for invalid input"""
        return {
            'indices': {
                'shannon_diversity': 0,
                'simpson_diversity': 0,
                'shannon_evenness': 0,
                'species_richness': 0,
                'dominance_index': 0,
                'margalef_richness': 0
            },
            'marine_metrics': {
                'novel_species_discovered': 0,
                'novel_species_ratio_percent': 0,
                'rare_species_count': 0,
                'dominant_species': 'None',
                'dominant_species_percentage': 0
            },
            'interpretations': {
                'shannon_interpretation': 'No data available',
                'simpson_interpretation': 'No data available', 
                'overall_diversity_assessment': 'No analysis possible',
                'ecosystem_health': 'Unable to assess'
            },
            'metadata': {
                'total_sequences_analyzed': 0,
                'unique_taxa_identified': 0,
                'calculation_timestamp': self._get_timestamp(),
                'methodology': 'No valid data for calculation'
            }
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()

    def generate_diversity_report(self, classification_results: Dict[str, Any]) -> str:
        """
        Generate a comprehensive biodiversity report in text format
        """
        metrics = self.calculate_metrics(classification_results)
        
        report = f"""
MARINE BIODIVERSITY ANALYSIS REPORT
{'='*50}
Generated: {metrics['metadata']['calculation_timestamp']}

SAMPLE OVERVIEW
{'-'*20}
Total Sequences Analyzed: {metrics['metadata']['total_sequences_analyzed']:,}
Unique Taxa Identified: {metrics['metadata']['unique_taxa_identified']}
Novel Species Discovered: {metrics['marine_metrics']['novel_species_discovered']}

DIVERSITY INDICES
{'-'*20}
Shannon Diversity Index (H): {metrics['indices']['shannon_diversity']:.4f}
  → {metrics['interpretations']['shannon_interpretation']}

Simpson Diversity Index (D): {metrics['indices']['simpson_diversity']:.4f}
  → {metrics['interpretations']['simpson_interpretation']}

Shannon Evenness Index (J): {metrics['indices']['shannon_evenness']:.4f}
Species Richness (S): {metrics['indices']['species_richness']}
Margalef Richness Index: {metrics['indices']['margalef_richness']:.4f}

MARINE-SPECIFIC METRICS
{'-'*20}
Novel Species Ratio: {metrics['marine_metrics']['novel_species_ratio_percent']:.1f}%
Rare Species Count: {metrics['marine_metrics']['rare_species_count']}
Dominant Species: {metrics['marine_metrics']['dominant_species']}
  → Represents {metrics['marine_metrics']['dominant_species_percentage']:.1f}% of community

ECOSYSTEM ASSESSMENT
{'-'*20}
Overall Diversity: {metrics['interpretations']['overall_diversity_assessment']}
Ecosystem Health: {metrics['interpretations']['ecosystem_health']}

METHODOLOGY
{'-'*20}
{metrics['metadata']['methodology']}

This report follows standard ecological protocols adapted for marine eDNA analysis.
For technical details, refer to the accompanying JSON metrics output.
        """
        
        return report.strip()