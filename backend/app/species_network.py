# species_network.py - Add this as backend/app/species_network.py

import numpy as np
from collections import Counter, defaultdict
from itertools import combinations
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NetworkNode:
    """A species node in the network"""
    species_id: str
    species_name: str
    abundance: int
    relative_abundance: float
    functional_group: str
    trophic_level: int
    node_size: float
    color_category: str

@dataclass
class NetworkEdge:
    """A connection between two species"""
    source: str
    target: str
    co_occurrence_strength: float
    relationship_type: str  # "frequent", "occasional", "rare"
    ecological_relationship: str  # "predator-prey", "competitive", "neutral", "mutualistic"
    edge_weight: float

@dataclass
class NetworkAnalysis:
    """Complete network analysis results"""
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    network_metrics: Dict
    community_structure: Dict
    ecological_insights: List[str]
    visualization_data: Dict

class SpeciesNetworkAnalyzer:
    """
    Creates ecological network visualizations showing species co-occurrence
    and potential ecological relationships.
    """
    
    def __init__(self):
        # Functional groups for marine ecosystems
        self.functional_groups = {
            'fish_predator': {
                'keywords': ['Gadus', 'Thunnus', 'Sebastes', 'Scomber'],
                'color': '#FF6B6B',  # Red
                'trophic_level': 4
            },
            'fish_planktivore': {
                'keywords': ['Clupea', 'Sardina', 'Engraulis'],
                'color': '#4ECDC4',  # Teal
                'trophic_level': 3
            },
            'fish_anadromous': {
                'keywords': ['Salmo', 'Oncorhynchus'],
                'color': '#45B7D1',  # Blue
                'trophic_level': 3
            },
            'zooplankton': {
                'keywords': ['Calanus', 'Copepoda', 'Euphausiacea', 'Mysida'],
                'color': '#96CEB4',  # Light Green
                'trophic_level': 2
            },
            'phytoplankton': {
                'keywords': ['Phaeodactylum', 'Thalassiosira', 'Skeletonema'],
                'color': '#FFEAA7',  # Yellow
                'trophic_level': 1
            },
            'invertebrate_filter': {
                'keywords': ['Mytilus', 'Crassostrea', 'Pecten'],
                'color': '#DDA0DD',  # Plum
                'trophic_level': 2
            },
            'invertebrate_predator': {
                'keywords': ['Cancer', 'Homarus', 'Asterias'],
                'color': '#FFA07A',  # Light Salmon
                'trophic_level': 3
            },
            'bacteria': {
                'keywords': ['Vibrio', 'Pseudomonas', 'Alteromonas'],
                'color': '#D3D3D3',  # Light Gray
                'trophic_level': 1
            },
            'unknown': {
                'keywords': [],
                'color': '#95A5A6',  # Gray
                'trophic_level': 2
            }
        }
        
        # Co-occurrence thresholds
        self.co_occurrence_thresholds = {
            'frequent': 0.6,    # Appear together in 60%+ of samples
            'occasional': 0.3,  # Appear together in 30-60% of samples
            'rare': 0.1         # Appear together in 10-30% of samples
        }

    def analyze_species_network(self, classification_results: Dict, 
                                sample_metadata: Optional[Dict] = None) -> NetworkAnalysis:
        """
        Create a species co-occurrence network from classification results.
        
        Args:
            classification_results: Your classifier output
            sample_metadata: Optional metadata about samples/locations
            
        Returns:
            NetworkAnalysis with nodes, edges, and visualization data
        """
        if not classification_results:
            return self._empty_network()
        
        logger.info("🕸️ Building species interaction network...")
        
        # Extract species information
        species_data = self._extract_species_data(classification_results)
        
        # Create nodes
        nodes = self._create_network_nodes(species_data)
        
        # Calculate co-occurrence and create edges
        edges = self._create_network_edges(species_data, nodes)
        
        # Calculate network metrics
        network_metrics = self._calculate_network_metrics(nodes, edges)
        
        # Detect community structure
        community_structure = self._detect_communities(nodes, edges)
        
        # Generate ecological insights
        ecological_insights = self._generate_ecological_insights(
            nodes, edges, network_metrics, community_structure
        )
        
        # Prepare visualization data
        visualization_data = self._prepare_visualization_data(nodes, edges, community_structure)
        
        logger.info(f"✅ Network created: {len(nodes)} species, {len(edges)} interactions")
        
        return NetworkAnalysis(
            nodes=nodes,
            edges=edges,
            network_metrics=network_metrics,
            community_structure=community_structure,
            ecological_insights=ecological_insights,
            visualization_data=visualization_data
        )

    def _extract_species_data(self, classification_results: Dict) -> Dict:
        """Extract and organize species data"""
        species_counts = Counter()
        species_info = defaultdict(lambda: {
            'otus': [],
            'total_abundance': 0,
            'avg_confidence': 0,
            'samples': set()
        })
        
        total_sequences = 0
        
        for otu_id, result in classification_results.items():
            if not isinstance(result, dict):
                continue
            
            species = result.get('predicted_species', 'Unknown')
            confidence = result.get('confidence_score', 0.5)
            
            # For this example, we'll treat each OTU as from the same "sample"
            sample_id = 'sample_1'
            
            species_counts[species] += 1
            species_info[species]['otus'].append(otu_id)
            species_info[species]['total_abundance'] += 1
            species_info[species]['samples'].add(sample_id)
            
            # Update average confidence
            curr_conf = species_info[species]['avg_confidence']
            curr_count = len(species_info[species]['otus']) - 1
            species_info[species]['avg_confidence'] = (
                (curr_conf * curr_count + confidence) / len(species_info[species]['otus'])
            )
            
            total_sequences += 1
        
        # Add relative abundance
        for species in species_info:
            species_info[species]['relative_abundance'] = (
                species_info[species]['total_abundance'] / total_sequences
            )
        
        return dict(species_info)

    def _create_network_nodes(self, species_data: Dict) -> List[NetworkNode]:
        """Create network nodes for each species"""
        nodes = []
        
        for species, info in species_data.items():
            functional_group = self._classify_functional_group(species)
            group_info = self.functional_groups[functional_group]
            
            base_size = max(10, np.log10(info['total_abundance'] + 1) * 20)
            
            node = NetworkNode(
                species_id=species.replace(' ', '_'),
                species_name=species,
                abundance=info['total_abundance'],
                relative_abundance=info['relative_abundance'],
                functional_group=functional_group,
                trophic_level=group_info['trophic_level'],
                node_size=base_size,
                color_category=group_info['color']
            )
            
            nodes.append(node)
        
        return nodes

    def _classify_functional_group(self, species_name: str) -> str:
        """Classify species into functional groups"""
        species_lower = species_name.lower()
        for group, info in self.functional_groups.items():
            if group == 'unknown':
                continue
            for keyword in info['keywords']:
                if keyword.lower() in species_lower:
                    return group
        return 'unknown'

    def _create_network_edges(self, species_data: Dict, nodes: List[NetworkNode]) -> List[NetworkEdge]:
        """Create edges based on co-occurrence patterns"""
        edges = []
        species_list = list(species_data.keys())
        
        for i, species1 in enumerate(species_list):
            for species2 in species_list[i+1:]:
                abundance1 = species_data[species1]['relative_abundance']
                abundance2 = species_data[species2]['relative_abundance']
                co_occurrence = 1 - abs(abundance1 - abundance2)
                
                if co_occurrence > self.co_occurrence_thresholds['rare']:
                    if co_occurrence > self.co_occurrence_thresholds['frequent']:
                        relationship_type = 'frequent'
                    elif co_occurrence > self.co_occurrence_thresholds['occasional']:
                        relationship_type = 'occasional'
                    else:
                        relationship_type = 'rare'
                    
                    ecological_rel = self._infer_ecological_relationship(species1, species2)
                    edge = NetworkEdge(
                        source=species1.replace(' ', '_'),
                        target=species2.replace(' ', '_'),
                        co_occurrence_strength=co_occurrence,
                        relationship_type=relationship_type,
                        ecological_relationship=ecological_rel,
                        edge_weight=co_occurrence * 5
                    )
                    edges.append(edge)
        
        return edges

    def _infer_ecological_relationship(self, species1: str, species2: str) -> str:
        """Infer ecological relationship between two species"""
        group1 = self._classify_functional_group(species1)
        group2 = self._classify_functional_group(species2)
        trophic1 = self.functional_groups[group1]['trophic_level']
        trophic2 = self.functional_groups[group2]['trophic_level']
        
        if abs(trophic1 - trophic2) == 1:
            return 'predator-prey'
        elif group1 == group2:
            return 'competitive'
        elif abs(trophic1 - trophic2) >= 2:
            return 'neutral'
        else:
            return 'mutualistic'

    def _calculate_network_metrics(self, nodes: List[NetworkNode], edges: List[NetworkEdge]) -> Dict:
        """Calculate basic network metrics"""
        num_nodes = len(nodes)
        num_edges = len(edges)
        if num_nodes == 0:
            return {}
        
        degree_count = defaultdict(int)
        for edge in edges:
            degree_count[edge.source] += 1
            degree_count[edge.target] += 1
        
        degrees = list(degree_count.values())
        avg_degree = np.mean(degrees) if degrees else 0
        max_edges = (num_nodes * (num_nodes - 1)) / 2
        density = num_edges / max_edges if max_edges > 0 else 0
        trophic_distribution = Counter(node.trophic_level for node in nodes)
        
        return {
            'num_species': num_nodes,
            'num_interactions': num_edges,
            'network_density': round(density, 3),
            'average_degree': round(avg_degree, 2),
            'max_degree': max(degrees) if degrees else 0,
            'trophic_levels': dict(trophic_distribution),
            'functional_groups': Counter(node.functional_group for node in nodes)
        }

    def _detect_communities(self, nodes: List[NetworkNode], edges: List[NetworkEdge]) -> Dict:
        """Simple community detection based on functional groups"""
        communities = defaultdict(list)
        for node in nodes:
            communities[node.functional_group].append({
                'species': node.species_name,
                'abundance': node.abundance,
                'trophic_level': node.trophic_level
            })
        
        community_metrics = {}
        for group, members in communities.items():
            total_abundance = sum(m['abundance'] for m in members)
            avg_trophic = np.mean([m['trophic_level'] for m in members])
            community_metrics[group] = {
                'size': len(members),
                'total_abundance': total_abundance,
                'average_trophic_level': round(avg_trophic, 2),
                'members': members
            }
        
        return {
            'communities': dict(communities),
            'community_metrics': community_metrics,
            'num_communities': len(communities)
        }

    def _generate_ecological_insights(self, nodes: List[NetworkNode], edges: List[NetworkEdge], 
                                      network_metrics: Dict, community_structure: Dict) -> List[str]:
        """Generate ecological insights from network analysis"""
        insights = []
        if network_metrics.get('network_density', 0) > 0.5:
            insights.append("🕸️ Highly connected ecosystem - species show strong co-occurrence patterns")
        elif network_metrics.get('network_density', 0) < 0.2:
            insights.append("🔗 Loosely connected ecosystem - species may be habitat specialists")
        
        trophic_levels = network_metrics.get('trophic_levels', {})
        if 4 in trophic_levels and 1 in trophic_levels:
            insights.append("🔺 Complete food web detected - from primary producers to top predators")
        elif max(trophic_levels.keys(), default=0) <= 2:
            insights.append("🌱 Producer-dominated ecosystem - limited predator presence")
        
        num_communities = community_structure.get('num_communities', 0)
        if num_communities >= 5:
            insights.append("🌈 High functional diversity - multiple ecological niches represented")
        elif num_communities <= 2:
            insights.append("⚠️ Low functional diversity - ecosystem may be simplified")
        
        if nodes:
            max_abundance = max(node.relative_abundance for node in nodes)
            if max_abundance > 0.5:
                dominant = next(node.species_name for node in nodes if node.relative_abundance == max_abundance)
                insights.append(f"👑 {dominant} dominates the ecosystem ({max_abundance:.1%} of sequences)")
        
        predator_edges = [e for e in edges if e.ecological_relationship == 'predator-prey']
        if len(predator_edges) > len(edges) * 0.3:
            insights.append("🦈 Strong predator-prey structure indicates active food web")
        
        return insights

    def _prepare_visualization_data(self, nodes: List[NetworkNode], edges: List[NetworkEdge], 
                                    community_structure: Dict) -> Dict:
        """Prepare data for frontend visualization"""
        vis_nodes = []
        for node in nodes:
            vis_nodes.append({
                'id': node.species_id,
                'label': node.species_name,
                'size': node.node_size,
                'color': node.color_category,
                'group': node.functional_group,
                'trophic_level': node.trophic_level,
                'abundance': node.abundance,
                'relative_abundance': f"{node.relative_abundance:.2%}"
            })
        
        vis_edges = []
        for edge in edges:
            vis_edges.append({
                'source': edge.source,
                'target': edge.target,
                'weight': edge.edge_weight,
                'type': edge.relationship_type,
                'ecological_relationship': edge.ecological_relationship,
                'strength': f"{edge.co_occurrence_strength:.2%}"
            })
        
        legend = []
        for group, info in self.functional_groups.items():
            if any(node.functional_group == group for node in nodes):
                legend.append({
                    'group': group,
                    'color': info['color'],
                    'trophic_level': info['trophic_level'],
                    'description': group.replace('_', ' ').title()
                })
        
        return {
            'nodes': vis_nodes,
            'edges': vis_edges,
            'legend': legend,
            'layout_config': {
                'physics': {
                    'enabled': True,
                    'repulsion': {'nodeDistance': 200},
                    'stabilization': {'iterations': 100}
                }
            }
        }

    def _empty_network(self) -> NetworkAnalysis:
        """Return empty network when no data available"""
        return NetworkAnalysis(
            nodes=[],
            edges=[],
            network_metrics={},
            community_structure={},
            ecological_insights=["No species data available for network analysis"],
            visualization_data={'nodes': [], 'edges': [], 'legend': []}
        )


# Integration function for your app.py
def create_species_network_analysis(classification_results: Dict) -> Dict:
    """
    Easy integration function to add to your app.py
    """
    analyzer = SpeciesNetworkAnalyzer()
    network_analysis = analyzer.analyze_species_network(classification_results)
    
    return {
        'network_metrics': network_analysis.network_metrics,
        'ecological_insights': network_analysis.ecological_insights,
        'community_structure': network_analysis.community_structure,
        'visualization_data': network_analysis.visualization_data,
        'summary': {
            'total_species': len(network_analysis.nodes),
            'total_interactions': len(network_analysis.edges),
            'functional_groups': len({node.functional_group for node in network_analysis.nodes}),
            'network_density': network_analysis.network_metrics.get('network_density', 0)
        }
    }
