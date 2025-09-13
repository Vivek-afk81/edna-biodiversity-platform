/**
 * eDNA Biodiversity Analysis Platform - Dashboard JavaScript
 * Handles Chart.js visualizations and real-time data updates
 * Optimized for performance and mobile responsiveness
 */

class BiodiversityDashboard {
    constructor() {
        this.charts = {};
        this.refreshInterval = 30000; // 30 seconds
        this.isLoading = false;
        this.init();
    }

    async init() {
        try {
            console.log('🚀 Initializing eDNA Biodiversity Dashboard...');
            
            // Load initial data
            await this.loadDashboardData();
            
            // Initialize charts
            this.initializeCharts();
            
            // Set up auto-refresh
            this.setupAutoRefresh();
            
            console.log('✅ Dashboard initialized successfully');
        } catch (error) {
            console.error('❌ Dashboard initialization failed:', error);
            this.showErrorMessage('Failed to initialize dashboard');
        }
    }

    async loadDashboardData() {
        if (this.isLoading) return;
        this.isLoading = true;
        
        try {
            const response = await fetch('/api/dashboard-data');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Update statistics
            this.updateStatistics(data.summary_stats);
            
            // Update charts
            this.updateCharts(data);
            
            // Update recent analyses table
            this.updateRecentAnalyses(data.recent_analyses);
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showErrorMessage('Failed to load dashboard data. Please check your connection.');
        } finally {
            this.isLoading = false;
        }
    }

    updateStatistics(stats) {
        const elements = {
            'total-analyses': stats.total_analyses || 0,
            'total-species': stats.total_species_identified || 0,
            'avg-diversity': (stats.average_diversity_index || 0).toFixed(3)
        };

        for (const [id, value] of Object.entries(elements)) {
            const element = document.getElementById(id);
            if (element) {
                // Animate counter
                this.animateCounter(element, value);
            }
        }
    }

    animateCounter(element, targetValue) {
        const startValue = parseFloat(element.textContent) || 0;
        const increment = (targetValue - startValue) / 20;
        let currentValue = startValue;

        const timer = setInterval(() => {
            currentValue += increment;
            if ((increment > 0 && currentValue >= targetValue) || 
                (increment < 0 && currentValue <= targetValue)) {
                currentValue = targetValue;
                clearInterval(timer);
            }

            // Format based on data type
            if (targetValue % 1 === 0) {
                element.textContent = Math.round(currentValue);
            } else {
                element.textContent = currentValue.toFixed(3);
            }
        }, 50);
    }

    initializeCharts() {
        this.initializeSpeciesChart();
        this.initializeTrendsChart();
    }

    initializeSpeciesChart() {
        const ctx = document.getElementById('species-chart');
        if (!ctx) return;

        this.charts.species = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', 
                        '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F',
                        '#BB8FCE', '#85C1E9', '#F8C471', '#82E0AA'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                aspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: { size: 12 },
                            generateLabels: function(chart) {
                                const data = chart.data;
                                if (data.labels.length && data.datasets.length) {
                                    return data.labels.map((label, i) => {
                                        const value = data.datasets[0].data[i];
                                        return {
                                            text: `${label} (${value})`,
                                            fillStyle: data.datasets[0].backgroundColor[i],
                                            strokeStyle: data.datasets[0].borderColor,
                                            lineWidth: data.datasets[0].borderWidth,
                                            hidden: false,
                                            index: i
                                        };
                                    });
                                }
                                return [];
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} sequences (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    initializeTrendsChart() {
        const ctx = document.getElementById('trends-chart');
        if (!ctx) return;

        this.charts.trends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Shannon Diversity Index',
                    data: [],
                    borderColor: '#4ECDC4',
                    backgroundColor: 'rgba(78, 205, 196, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#4ECDC4',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                aspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        labels: {
                            font: { size: 14, weight: 'bold' }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#4ECDC4',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Date',
                            font: { size: 14, weight: 'bold' }
                        },
                        grid: { color: 'rgba(0, 0, 0, 0.1)' }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Shannon Index',
                            font: { size: 14, weight: 'bold' }
                        },
                        beginAtZero: true,
                        grid: { color: 'rgba(0, 0, 0, 0.1)' }
                    }
                }
            }
        });
    }

    updateCharts(data) {
        this.updateSpeciesChart(data.species_distribution);
        this.updateTrendsChart(data.biodiversity_trends);
    }

    updateSpeciesChart(speciesData) {
        if (!this.charts.species || !speciesData) {
            return;
        }

        // Handle both array and object formats
        let processedData = [];
        if (Array.isArray(speciesData)) {
            processedData = speciesData.slice(0, 10); // Limit to top 10
        } else if (typeof speciesData === 'object') {
            // Convert taxonomic_classification object to array format
            processedData = Object.entries(speciesData).map(([otu, info]) => ({
                species: otu,
                total_sequences: info.num_sequences || info.count || 1
            })).slice(0, 10);
        }

        const labels = processedData.map(item => {
            const name = item.species || item.species_name || item.otu || 'Unknown';
            return name.length > 20 ? name.substring(0, 17) + '...' : name;
        });
        
        const data = processedData.map(item => 
            item.total_sequences || item.total_count || item.count || 0
        );

        this.charts.species.data.labels = labels;
        this.charts.species.data.datasets[0].data = data;
        this.charts.species.update('active');
    }

    updateTrendsChart(trendsData) {
        if (!this.charts.trends || !trendsData) {
            return;
        }

        const dates = trendsData.dates || [];
        const shannonValues = trendsData.shannon_values || [];

        // Format dates for display
        const formattedDates = dates.map(date => {
            const d = new Date(date);
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });

        this.charts.trends.data.labels = formattedDates;
        this.charts.trends.data.datasets[0].data = shannonValues;
        this.charts.trends.update('active');
    }

    updateRecentAnalyses(analyses) {
        const loadingElement = document.getElementById('analyses-loading');
        const contentElement = document.getElementById('analyses-content');
        const tbody = document.getElementById('analyses-tbody');

        if (!tbody) return;

        // Hide loading, show content
        if (loadingElement) loadingElement.style.display = 'none';
        if (contentElement) contentElement.style.display = 'block';

        // Clear existing rows
        tbody.innerHTML = '';

        if (!analyses || analyses.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; color: #666; padding: 2rem;">
                        No recent analyses found. Upload a FASTA file to get started!
                    </td>
                </tr>
            `;
            return;
        }

        // Populate table with analyses
        analyses.forEach(analysis => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${analysis.filename || 'Unknown'}</td>
                <td>${new Date(analysis.timestamp).toLocaleDateString()}</td>
                <td>${analysis.total_sequences || 0}</td>
                <td>${analysis.taxa_found || 0}</td>
                <td>${analysis.novel_species || 0}</td>
                <td>${(analysis.shannon_index || 0).toFixed(3)}</td>
                <td><span class="status-badge status-completed">Completed</span></td>
            `;
            tbody.appendChild(row);
        });
    }

    setupAutoRefresh() {
        setInterval(() => {
            if (!document.hidden) { // Only refresh when page is visible
                this.loadDashboardData();
            }
        }, this.refreshInterval);
    }

    showErrorMessage(message) {
        const existingError = document.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;

        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(errorDiv, container.firstChild);
        }
    }

    // Method to update results from upload page
    updateLatestResults(result) {
        // Update taxonomic classification display
        const classificationElement = document.getElementById('classification-json');
        if (classificationElement) {
            classificationElement.textContent = JSON.stringify(result.taxonomic_classification, null, 2);
        }

        // Update biodiversity metrics display
        if (result.biodiversity_metrics) {
            const shannonElement = document.getElementById('metric-shannon');
            const simpsonElement = document.getElementById('metric-simpson');
            const phyloElement = document.getElementById('metric-phylo');

            if (shannonElement) shannonElement.textContent = result.biodiversity_metrics.shannon_diversity.toFixed(3);
            if (simpsonElement) simpsonElement.textContent = result.biodiversity_metrics.simpson_index.toFixed(3);
            if (phyloElement) phyloElement.textContent = result.biodiversity_metrics.phylogenetic_diversity.toFixed(3);
        }

        // Update species chart with new data
        if (result.taxonomic_classification) {
            this.updateSpeciesChart(result.taxonomic_classification);
        }
    }
}

// Global function for upload page integration
function showResults(result) {
    const progressContainer = document.getElementById('progress-container');
    const resultsPreview = document.getElementById('results-preview');
    const quickStats = document.getElementById('quick-stats');

    // Hide progress, show results
    if (progressContainer) progressContainer.style.display = 'none';
    if (resultsPreview) resultsPreview.style.display = 'block';

    // Populate quick stats using the correct API response structure
    if (quickStats) {
        quickStats.innerHTML = `
            <div class="quick-stat">
                <div class="quick-stat-number">${result.total_sequences}</div>
                <div class="quick-stat-label">Sequences</div>
            </div>
            <div class="quick-stat">
                <div class="quick-stat-number">${Object.keys(result.taxonomic_classification || {}).length}</div>
                <div class="quick-stat-label">OTUs</div>
            </div>
            <div class="quick-stat">
                <div class="quick-stat-number">${(result.biodiversity_metrics?.shannon_diversity || 0).toFixed(2)}</div>
                <div class="quick-stat-label">Shannon Index</div>
            </div>
            <div class="quick-stat">
                <div class="quick-stat-number">${(result.biodiversity_metrics?.simpson_index || 0).toFixed(2)}</div>
                <div class="quick-stat-label">Simpson Index</div>
            </div>
        `;
    }

    // If dashboard instance exists, update it with new results
    if (window.dashboardInstance) {
        window.dashboardInstance.updateLatestResults(result);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardInstance = new BiodiversityDashboard();
});

// Handle visibility change for efficient auto-refresh
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && window.dashboardInstance) {
        window.dashboardInstance.loadDashboardData();
    }
});