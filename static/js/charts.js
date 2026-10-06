// Sanskriti University - Asset Recovery Analytics Charts
// Renders Chart.js visual graphs for Reports and Admin Dashboards

function initReportsCharts(statsData) {
    if (!statsData) return;

    // 1. Category Breakdown Chart (Lost vs Found)
    const catCanvas = document.getElementById('categoryBreakdownChart');
    if (catCanvas && statsData.categories) {
        new Chart(catCanvas, {
            type: 'bar',
            data: {
                labels: statsData.categories.labels,
                datasets: [
                    {
                        label: 'Lost Reports',
                        data: statsData.categories.lost_counts,
                        backgroundColor: '#ef4444',
                        borderRadius: 6
                    },
                    {
                        label: 'Found Reports',
                        data: statsData.categories.found_counts,
                        backgroundColor: '#10b981',
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }

    // 2. Campus Hotspots Chart (Horizontal Bar)
    const hotspotCanvas = document.getElementById('campusHotspotsChart');
    if (hotspotCanvas && statsData.hotspots) {
        new Chart(hotspotCanvas, {
            type: 'bar',
            indexAxis: 'y',
            data: {
                labels: statsData.hotspots.labels,
                datasets: [{
                    label: 'Reported Incidents',
                    data: statsData.hotspots.counts,
                    backgroundColor: [
                        '#002147', '#0d3b66', '#c99700', '#2563eb',
                        '#7c3aed', '#059669', '#d97706', '#dc2626'
                    ],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }

    // 3. Lifecycle Status Distribution (Doughnut Chart)
    const statusCanvas = document.getElementById('statusDistributionChart');
    if (statusCanvas && statsData.statuses) {
        new Chart(statusCanvas, {
            type: 'doughnut',
            data: {
                labels: statsData.statuses.labels,
                datasets: [{
                    data: statsData.statuses.counts,
                    backgroundColor: [
                        '#ef4444', // Lost
                        '#10b981', // Found
                        '#f59e0b', // Under Claim
                        '#6366f1', // Verified
                        '#059669', // Returned
                        '#64748b'  // Closed
                    ],
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right' }
                },
                cutout: '65%'
            }
        });
    }

    // 4. Monthly Recovery Trend Chart (Line Chart)
    const trendCanvas = document.getElementById('recoveryTrendChart');
    if (trendCanvas && statsData.trends) {
        new Chart(trendCanvas, {
            type: 'line',
            data: {
                labels: statsData.trends.months,
                datasets: [
                    {
                        label: 'Total Reports',
                        data: statsData.trends.total_reports,
                        borderColor: '#002147',
                        backgroundColor: 'rgba(0, 33, 71, 0.08)',
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Assets Successfully Recovered',
                        data: statsData.trends.recovered,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.12)',
                        tension: 0.3,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
}
