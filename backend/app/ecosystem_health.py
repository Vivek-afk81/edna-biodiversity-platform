# ecosystem_health.py - Add this as a new file in your backend/app/ folder

import numpy as np
from collections import Counter
import math
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class EcosystemHealth:
    """Comprehensive ecosystem health assessment"""
    overall_score: float  # 0-100 scale
    health_category: str  # "Excellent", "Good", "Fair", "Poor", "Critical"
    biodiversity_score: float
    stability_score: float
    rarity_score: float
    functional_diversity_score: float
    recommendations: List[str]
    detailed_metrics: Dict

class EcosystemHealthAnalyzer:
    """
    Advanced ecosystem health calculator that combines multiple biodiversity
    metrics into meaningful ecological insights.
    """
    
    def __init__(self):
        # Reference values for ecosystem health thresholds
        self.health_thresholds = {
            "excellent": 85,
            "good": 70,
            "fair": 55,
            "poor": 40,
            "critical": 0
        }
        
        # Expected species for different ecosystem types (simplified)
        self.ecosystem_references = {
            "marine_temperate": {
                "expected_species": ["Gadus_morhua", "Salmo_salar", "Sebastes_norvegicus"],
                "indicator_species": ["Gadus_morhua"],
                "invasive_alerts": ["Mnemiopsis_leidyi"]
            },
            "marine_arctic": {
                "expected_species": ["Gadus_morhua", "Boreogadus_saida", "Calanus_finmarchicus"],
                "indicator_species": ["Calanus_finmarchicus"],
                "invasive_alerts": []
            }
        }

    def calculate_proper_biodiversity_metrics(self, classification_results: Dict) -> Dict:
        """
        Calculate REAL Shannon and Simpson indices from classification results.
        This replaces your placeholder calculations!
        """
        if not classification_results:
            return {
                "shannon_diversity": 0.0,
                "simpson_index": 0.0,
                "evenness": 0.0,
                "species_richness": 0,
                "dominance": 0.0
            }
        
        # Count species occurrences
        species_counts = Counter()
        total_sequences = 0
        
        for otu_id, result in classification_results.items():
            if isinstance(result, dict):
                species = result.get('predicted_species', 'Unknown')
                species_counts[species] += 1
                total_sequences += 1
        
        if total_sequences == 0:
            return self._empty_metrics()
        
        # Calculate proportions
        proportions = [count / total_sequences for count in species_counts.values()]
        
        # Shannon Diversity Index: H' = -Σ(p * ln(p))
        shannon = -sum(p * math.log(p) for p in proportions if p > 0)
        
        # Simpson Index: 1 - Σ(p²)
        simpson = 1 - sum(p**2 for p in proportions)
        
        # Evenness: H' / ln(S) where S is species richness
        species_richness = len(species_counts)
        evenness = shannon / math.log(species_richness) if species_richness > 1 else 1.0
        
        # Dominance: proportion of most common species
        dominance = max(proportions) if proportions else 0.0
        
        return {
            "shannon_diversity": round(shannon, 3),
            "simpson_index": round(simpson, 3),
            "evenness": round(evenness, 3),
            "species_richness": species_richness,
            "dominance": round(dominance, 3)
        }

    def analyze_ecosystem_health(self, classification_results: Dict, 
                               ecosystem_type: str = "marine_temperate") -> EcosystemHealth:
        """
        Comprehensive ecosystem health analysis combining multiple factors.
        """
        # Get proper biodiversity metrics
        biodiv_metrics = self.calculate_proper_biodiversity_metrics(classification_results)
        
        # Calculate component scores
        biodiversity_score = self._calculate_biodiversity_score(biodiv_metrics)
        stability_score = self._calculate_stability_score(classification_results, biodiv_metrics)
        rarity_score = self._calculate_rarity_score(classification_results)
        functional_diversity_score = self._calculate_functional_diversity(classification_results)
        
        # Combine into overall score (weighted average)
        overall_score = (
            biodiversity_score * 0.35 +      # Biodiversity is most important
            stability_score * 0.25 +         # Ecosystem stability
            rarity_score * 0.20 +            # Presence of rare/indicator species
            functional_diversity_score * 0.20 # Functional diversity
        )
        
        # Determine health category
        health_category = self._get_health_category(overall_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_score, biodiv_metrics, classification_results, ecosystem_type
        )
        
        # Detailed metrics for advanced users
        detailed_metrics = {
            "biodiversity_metrics": biodiv_metrics,
            "component_scores": {
                "biodiversity": round(biodiversity_score, 2),
                "stability": round(stability_score, 2),
                "rarity": round(rarity_score, 2),
                "functional_diversity": round(functional_diversity_score, 2)
            },
            "species_composition": self._analyze_species_composition(classification_results),
            "ecological_indicators": self._check_ecological_indicators(classification_results, ecosystem_type)
        }
        
        return EcosystemHealth(
            overall_score=round(overall_score, 1),
            health_category=health_category,
            biodiversity_score=round(biodiversity_score, 1),
            stability_score=round(stability_score, 1),
            rarity_score=round(rarity_score, 1),
            functional_diversity_score=round(functional_diversity_score, 1),
            recommendations=recommendations,
            detailed_metrics=detailed_metrics
        )

    def _calculate_biodiversity_score(self, biodiv_metrics: Dict) -> float:
        """Score based on Shannon diversity and evenness (0-100)"""
        shannon = biodiv_metrics.get('shannon_diversity', 0)
        evenness = biodiv_metrics.get('evenness', 0)
        richness = biodiv_metrics.get('species_richness', 0)
        
        # Normalize Shannon (typical range 0-4 for most ecosystems)
        shannon_norm = min(shannon / 4.0, 1.0) * 50
        
        # Evenness score (0-1 already normalized)
        evenness_score = evenness * 30
        
        # Richness bonus (diminishing returns)
        richness_bonus = min(math.log(richness + 1) / math.log(20), 1.0) * 20
        
        return shannon_norm + evenness_score + richness_bonus

    def _calculate_stability_score(self, classification_results: Dict, biodiv_metrics: Dict) -> float:
        """Score based on ecosystem stability indicators (0-100)"""
        dominance = biodiv_metrics.get('dominance', 0)
        evenness = biodiv_metrics.get('evenness', 0)
        
        # Lower dominance = higher stability
        dominance_score = (1 - dominance) * 50
        
        # Higher evenness = higher stability
        evenness_score = evenness * 50
        
        return dominance_score + evenness_score

    def _calculate_rarity_score(self, classification_results: Dict) -> float:
        """Score based on presence of rare or indicator species (0-100)"""
        if not classification_results:
            return 0.0
        
        species_counts = Counter()
        total_sequences = 0
        
        for otu_id, result in classification_results.items():
            if isinstance(result, dict):
                species = result.get('predicted_species', 'Unknown')
                confidence = result.get('confidence_score', 0.5)
                species_counts[species] += 1
                total_sequences += 1
        
        # Calculate rarity based on species frequency distribution
        frequencies = list(species_counts.values())
        if not frequencies:
            return 0.0
        
        # Presence of singletons (rare species) is good for biodiversity
        singletons = sum(1 for freq in frequencies if freq == 1)
        singleton_score = min(singletons / len(frequencies), 0.5) * 100
        
        # Presence of very rare species (< 5% of total)
        rare_species = sum(1 for freq in frequencies if freq / total_sequences < 0.05)
        rare_score = min(rare_species / len(frequencies), 0.5) * 100
        
        return (singleton_score + rare_score) / 2

    def _calculate_functional_diversity(self, classification_results: Dict) -> float:
        """Score based on functional group diversity (0-100)"""
        if not classification_results:
            return 0.0
        
        # Simplified functional groups based on species names
        functional_groups = {
            'fish_predator': ['Gadus', 'Thunnus', 'Sebastes'],
            'fish_anadromous': ['Salmo'],
            'zooplankton': ['Calanus', 'Copepoda'],
            'invertebrate': ['Mollusca', 'Crustacea'],
            'primary_producer': ['Phytoplankton', 'Algae']
        }
        
        present_groups = set()
        
        for otu_id, result in classification_results.items():
            if isinstance(result, dict):
                species = result.get('predicted_species', 'Unknown')
                
                # Check which functional group this species belongs to
                for group, indicators in functional_groups.items():
                    if any(indicator in species for indicator in indicators):
                        present_groups.add(group)
                        break
        
        # Score based on functional group diversity
        max_groups = len(functional_groups)
        diversity_score = (len(present_groups) / max_groups) * 100
        
        return diversity_score

    def _get_health_category(self, score: float) -> str:
        """Convert numerical score to health category"""
        if score >= self.health_thresholds["excellent"]:
            return "Excellent"
        elif score >= self.health_thresholds["good"]:
            return "Good"
        elif score >= self.health_thresholds["fair"]:
            return "Fair"
        elif score >= self.health_thresholds["poor"]:
            return "Poor"
        else:
            return "Critical"

    def _generate_recommendations(self, score: float, biodiv_metrics: Dict, 
                                classification_results: Dict, ecosystem_type: str) -> List[str]:
        """Generate actionable recommendations based on health score"""
        recommendations = []
        
        # Based on overall score
        if score < 40:
            recommendations.append("🚨 Immediate conservation action required - ecosystem shows signs of severe degradation")
            recommendations.append("🔍 Conduct detailed species inventory to identify missing key species")
        elif score < 55:
            recommendations.append("⚠️ Ecosystem under stress - monitor key indicator species closely")
            recommendations.append("🌊 Check for pollution sources or habitat disturbance")
        elif score < 70:
            recommendations.append("📊 Ecosystem stable but could be improved")
            recommendations.append("🐟 Consider habitat enhancement measures")
        elif score < 85:
            recommendations.append("✅ Healthy ecosystem - maintain current protection measures")
            recommendations.append("📈 Continue regular monitoring to track trends")
        else:
            recommendations.append("🌟 Exceptional biodiversity - prioritize for long-term protection")
            recommendations.append("🧬 Consider this area for biodiversity research and seed banking")
        
        # Specific recommendations based on metrics
        shannon = biodiv_metrics.get('shannon_diversity', 0)
        if shannon < 1.0:
            recommendations.append("📉 Low species diversity detected - investigate potential causes")
        
        dominance = biodiv_metrics.get('dominance', 0)
        if dominance > 0.7:
            recommendations.append("⚖️ High species dominance - ecosystem may be unbalanced")
        
        # Functional diversity recommendations
        species_list = [result.get('predicted_species', 'Unknown') 
                       for result in classification_results.values() if isinstance(result, dict)]
        
        if not any('Calanus' in species for species in species_list):
            recommendations.append("🦐 Key zooplankton species missing - check food web integrity")
        
        return recommendations

    def _analyze_species_composition(self, classification_results: Dict) -> Dict:
        """Analyze the composition of species found"""
        if not classification_results:
            return {}
        
        species_info = {}
        confidence_scores = []
        
        for otu_id, result in classification_results.items():
            if isinstance(result, dict):
                species = result.get('predicted_species', 'Unknown')
                confidence = result.get('confidence_score', 0.5)
                confidence_scores.append(confidence)
                
                if species not in species_info:
                    species_info[species] = {
                        'count': 0,
                        'avg_confidence': 0,
                        'otu_ids': []
                    }
                
                species_info[species]['count'] += 1
                species_info[species]['otu_ids'].append(otu_id)
        
        # Calculate average confidence per species
        for species in species_info:
            species_otus = species_info[species]['otu_ids']
            confidences = [classification_results[otu].get('confidence_score', 0.5) 
                          for otu in species_otus if otu in classification_results]
            species_info[species]['avg_confidence'] = round(np.mean(confidences), 3) if confidences else 0.5
        
        return {
            'species_details': species_info,
            'total_species': len(species_info),
            'avg_identification_confidence': round(np.mean(confidence_scores), 3) if confidence_scores else 0.5
        }

    def _check_ecological_indicators(self, classification_results: Dict, ecosystem_type: str) -> Dict:
        """Check for presence of ecological indicator species"""
        indicators = {
            'keystone_species': [],
            'indicator_species': [],
            'invasive_species': [],
            'endangered_species': []
        }
        
        species_found = [result.get('predicted_species', 'Unknown') 
                        for result in classification_results.values() if isinstance(result, dict)]
        
        # Check against reference ecosystem
        if ecosystem_type in self.ecosystem_references:
            ref_ecosystem = self.ecosystem_references[ecosystem_type]
            
            # Check for indicator species
            for species in species_found:
                if species in ref_ecosystem.get('indicator_species', []):
                    indicators['indicator_species'].append(species)
                
                if species in ref_ecosystem.get('invasive_alerts', []):
                    indicators['invasive_species'].append(species)
        
        return indicators

    def _empty_metrics(self) -> Dict:
        """Return empty metrics when no data available"""
        return {
            "shannon_diversity": 0.0,
            "simpson_index": 0.0,
            "evenness": 0.0,
            "species_richness": 0,
            "dominance": 0.0
        }


# Integration function for your existing app.py
def get_ecosystem_health_analysis(classification_results: Dict) -> Dict:
    """
    Easy integration function - just replace your biodiversity calculation
    with this function call in app.py
    """
    analyzer = EcosystemHealthAnalyzer()
    
    # Get proper biodiversity metrics (replaces your placeholders)
    biodiv_metrics = analyzer.calculate_proper_biodiversity_metrics(classification_results)
    
    # Get comprehensive ecosystem health analysis
    health_analysis = analyzer.analyze_ecosystem_health(classification_results)
    
    return {
        "biodiversity_metrics": biodiv_metrics,
        "ecosystem_health": {
            "overall_score": health_analysis.overall_score,
            "health_category": health_analysis.health_category,
            "component_scores": {
                "biodiversity": health_analysis.biodiversity_score,
                "stability": health_analysis.stability_score,
                "rarity": health_analysis.rarity_score,
                "functional_diversity": health_analysis.functional_diversity_score
            },
            "recommendations": health_analysis.recommendations
        },
        "advanced_metrics": health_analysis.detailed_metrics
    }