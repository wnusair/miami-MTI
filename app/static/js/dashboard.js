/**
 * Dashboard JavaScript for MTI (Miami Telemetry Interface)
 * Handles chart rendering, data fetching, and real-time updates
 */

// Chart.js default configuration
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.color = '#757575';

// Color palette matching Miami University theme
const COLORS = {
    miamiRed: '#C3142D',
    foundationBlack: '#000000',
    academicGray: '#757575',
    lightGray: '#E5E7EB',
    success: '#059669',
    warning: '#D97706'
};

// Chart instances
let liveChart = null;
let healthChart = null;

// Update interval (5 seconds)
const UPDATE_INTERVAL = 5000;

/**
 * Initialize the dashboard on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeDatePickers();
    initializeCharts();
    loadAllData();
    
    // Start auto-refresh
    setInterval(loadAllData, UPDATE_INTERVAL);
});

/**
 * Initialize date pickers with default values
 * Note: Date pickers are left empty by default so export includes all data.
 * Users can optionally set a date range to filter the export.
 */
function initializeDatePickers() {
    // Date pickers are intentionally left empty by default
    // This ensures the export includes all available data
    // Users can manually set a date range if they want to filter
    
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    
    // Set max date to current time to prevent future dates
    if (startDateInput) {
        startDateInput.max = formatDateTimeLocal(new Date());
    }
    if (endDateInput) {
        endDateInput.max = formatDateTimeLocal(new Date());
    }
}

/**
 * Format date for datetime-local input
 */
function formatDateTimeLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

/**
 * Initialize Chart.js charts
 */
function initializeCharts() {
    // Live Sensor Feed Chart
    const liveChartCanvas = document.getElementById('liveChart');
    if (liveChartCanvas) {
        const ctx = liveChartCanvas.getContext('2d');
        liveChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            boxWidth: 6
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: COLORS.lightGray
                        }
                    },
                    y: {
                        grid: {
                            color: COLORS.lightGray
                        }
                    }
                }
            }
        });
    }
    
    // Device Health Chart
    const healthChartCanvas = document.getElementById('healthChart');
    if (healthChartCanvas) {
        const ctx = healthChartCanvas.getContext('2d');
        healthChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Latest Value',
                    data: [],
                    backgroundColor: COLORS.miamiRed,
                    borderColor: COLORS.miamiRed,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        grid: {
                            color: COLORS.lightGray
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

/**
 * Load all dashboard data
 */
async function loadAllData() {
    await Promise.all([
        loadSensorData(),
        loadKPIs(),
        loadHistoricalLogs(),
        loadDeviceHealth()
    ]);
}

/**
 * Refresh data manually
 */
function refreshData() {
    loadAllData();
}

/**
 * Load live sensor data for the line chart
 */
async function loadSensorData() {
    if (!liveChart) return;
    
    try {
        const response = await fetch('/api/sensor-data?hours=1&limit=100');
        const data = await response.json();
        
        if (data.length === 0) {
            return;
        }
        
        // Group data by sensor
        const sensorGroups = {};
        data.forEach(item => {
            if (!sensorGroups[item.sensor_name]) {
                sensorGroups[item.sensor_name] = [];
            }
            sensorGroups[item.sensor_name].push(item);
        });
        
        // Get unique timestamps
        const timestamps = [...new Set(data.map(d => d.timestamp))].sort();
        const labels = timestamps.map(t => {
            const date = new Date(t);
            return date.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
            });
        });
        
        // Create datasets
        const colors = [COLORS.miamiRed, '#1D4ED8', '#059669', '#7C3AED', '#D97706'];
        const datasets = Object.keys(sensorGroups).map((sensorName, index) => {
            const sensorData = sensorGroups[sensorName];
            const values = timestamps.map(timestamp => {
                const point = sensorData.find(d => d.timestamp === timestamp);
                return point ? point.value : null;
            });
            
            return {
                label: sensorName,
                data: values,
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '20',
                borderWidth: 2,
                fill: false,
                tension: 0.1,
                pointRadius: 2
            };
        });
        
        liveChart.data.labels = labels;
        liveChart.data.datasets = datasets;
        liveChart.update('none');
        
    } catch (error) {
        console.error('Error loading sensor data:', error);
    }
}

/**
 * Load KPI statistics
 */
async function loadKPIs() {
    try {
        const response = await fetch('/api/sensor-data/stats?hours=1');
        const stats = await response.json();
        
        const totalReadings = document.getElementById('kpi-total-readings');
        const sensorCount = document.getElementById('kpi-sensor-count');
        const avgValue = document.getElementById('kpi-avg-value');
        const statusOk = document.getElementById('kpi-status-ok');
        
        if (totalReadings) totalReadings.textContent = stats.total_readings || 0;
        if (sensorCount) sensorCount.textContent = stats.sensor_count || 0;
        if (avgValue) avgValue.textContent = stats.avg_value || 0;
        if (statusOk) statusOk.textContent = stats.status_summary?.OK || 0;
        
    } catch (error) {
        console.error('Error loading KPIs:', error);
    }
}

/**
 * Load historical logs for the data table
 */
async function loadHistoricalLogs() {
    const tbody = document.getElementById('logs-tbody');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/sensor-data?hours=24&limit=50');
        const data = await response.json();
        
        tbody.innerHTML = '';
        
        if (data.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="5" class="text-center">No data available</td>';
            tbody.appendChild(row);
            return;
        }
        
        // Reverse to show newest first
        data.reverse().forEach(item => {
            const row = document.createElement('tr');
            const timestamp = new Date(item.timestamp).toLocaleString();
            const statusClass = item.status === 'OK' ? 'status-ok' : 
                               item.status === 'WARNING' ? 'status-warning' : 'status-error';
            
            row.innerHTML = `
                <td>${timestamp}</td>
                <td>${item.sensor_name}</td>
                <td>${item.value.toFixed(2)}</td>
                <td>${item.unit}</td>
                <td class="${statusClass}">${item.status}</td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error loading historical logs:', error);
    }
}

/**
 * Load device health data for the bar chart
 */
async function loadDeviceHealth() {
    if (!healthChart) return;
    
    try {
        const response = await fetch('/api/sensor-data/latest');
        const data = await response.json();
        
        if (data.length === 0) {
            return;
        }
        
        const labels = data.map(d => d.sensor_name);
        const values = data.map(d => d.value);
        const colors = data.map(d => 
            d.status === 'OK' ? COLORS.success : 
            d.status === 'WARNING' ? COLORS.warning : COLORS.miamiRed
        );
        
        healthChart.data.labels = labels;
        healthChart.data.datasets[0].data = values;
        healthChart.data.datasets[0].backgroundColor = colors;
        healthChart.data.datasets[0].borderColor = colors;
        healthChart.update('none');
        
    } catch (error) {
        console.error('Error loading device health:', error);
    }
}

/**
 * Download XLSX export
 */
function downloadExport() {
    const startDate = document.getElementById('start-date')?.value;
    const endDate = document.getElementById('end-date')?.value;
    
    let url = '/api/export';
    const params = [];
    
    if (startDate) {
        params.push(`start_date=${encodeURIComponent(startDate)}`);
    }
    if (endDate) {
        params.push(`end_date=${encodeURIComponent(endDate)}`);
    }
    
    if (params.length > 0) {
        url += '?' + params.join('&');
    }
    
    window.location.href = url;
}
