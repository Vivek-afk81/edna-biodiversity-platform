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
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Shannon Index',
                            font: { size: 14, weight: 'bold' }
                        },
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
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
        if (!this.charts.species || !speciesData || !Array.isArray(speciesData)) {
            return;
        }

        // Limit to top 10 species for readability
        const topSpecies = speciesData.slice(0, 10);

        const labels = topSpecies.map(item => {
            const name = item.species || item.species_name || 'Unknown';
            return name.length > 20 ? name.substring(0, 17) + '...' : name;
        });

        const data = topSpecies.map(item => item.total_sequences || item.total_count || 0);

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
                    <td colspan="7" style="text-align: center; padding: 2rem; color: #666;">
                        No analyses found. Upload your first eDNA sample to get started!
                    </td>
                </tr>
            `;
            return;
        }

        // Add analysis rows
        analyses.forEach(analysis => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${this.truncateFilename(analysis.filename || 'Unknown')}</td>
                <td>${this.formatDateTime(analysis.timestamp || analysis.upload_timestamp)}</td>
                <td>${analysis.total_sequences || 0}</td>
                <td>${analysis.unique_taxa || analysis.unique_taxa_count || 0}</td>
                <td>${analysis.novel_species || analysis.novel_species_count || 0}</td>
                <td>${(analysis.shannon_index || 0).toFixed(3)}</td>
                <td><span class="status-badge status-completed">${analysis.status || 'Completed'}</span></td>
            `;
            tbody.appendChild(row);
        });
    }

    truncateFilename(filename) {
        if (filename.length <= 25) return filename;
        const parts = filename.split('.');
        const ext = parts.pop();
        const name = parts.join('.');
        return name.substring(0, 20) + '...' + ext;
    }

    formatDateTime(timestamp) {
        if (!timestamp) return 'Unknown';

        try {
            const date = new Date(timestamp);
            return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return 'Invalid date';
        }
    }

    setupAutoRefresh() {
        setInterval(() => {
            this.loadDashboardData();
        }, this.refreshInterval);

        // Refresh when page becomes visible again
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.loadDashboardData();
            }
        });
    }

    showErrorMessage(message) {
        const container = document.querySelector('.container');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <strong>⚠️ Error:</strong> ${message}
            <button onclick="location.reload()" style="float: right; background: #721c24; color: white; border: none; padding: 0.3rem 0.8rem; border-radius: 4px; cursor: pointer;">
                Reload Page
            </button>
        `;

        container.insertBefore(errorDiv, container.firstChild);

        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 10000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new BiodiversityDashboard();
});

// Health check function
async function checkSystemHealth() {
    try {
        const response = await fetch('/health');
        const health = await response.json();

        if (health.status === 'healthy') {
            console.log('✅ System health check passed');
        } else {
            console.warn('⚠️ System health check warning:', health);
        }
    } catch (error) {
        console.error('❌ System health check failed:', error);
    }
}

// Run health check every 5 minutes
setInterval(checkSystemHealth, 300000);
