class ChartConfig {
    constructor(id, label, dataKey, threshold, unit) {
        this.id = id;
        this.label = label;
        this.dataKey = dataKey;
        this.threshold = threshold;
        this.unit = unit;
    }
}

class ChartFactory {
    createHealthChart(ctx, label, labels, data, threshold, unit) {
        const hasThreshold = Number.isFinite(threshold);

        // Helper to build the dynamic "Red-Below-Threshold" gradient
        const getGradient = (context) => {
            const chart = context.chart;
            const {ctx, chartArea, scales} = chart;

            if (!chartArea || !scales.y) return 'rgba(54, 162, 235, 0.2)';
            if (!hasThreshold) {
                return 'rgba(54, 162, 235, 0.25)';
            }

            const thresholdPixel = scales.y.getPixelForValue(threshold);
            
            // Calculate the percentage of the height where the line sits
            let stopPoint = (thresholdPixel - chartArea.top) / (chartArea.bottom - chartArea.top);
            stopPoint = Math.max(0, Math.min(1, stopPoint));

            const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
            
            // 0 is the TOP of the chart (Wet/High values)
            gradient.addColorStop(0, 'rgba(54, 162, 235, 0.4)');    // Top: Solid Blue
            gradient.addColorStop(stopPoint, 'rgba(54, 162, 235, 0.1)'); // Above line: Fading Blue
            
            // stopPoint is the THRESHOLD line
            gradient.addColorStop(stopPoint, 'rgba(255, 99, 132, 0.2)'); // Below line: Faint Red
            gradient.addColorStop(1, 'rgba(255, 99, 132, 0.6)');    // Bottom: Deep Red (Dry)
            
            return gradient;
        };

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    fill: true,
                    backgroundColor: (context) => getGradient(context),
                    borderColor: 'rgba(54, 162, 235, 0.8)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: label,
                        color: '#666',
                        font: {
                            size: 18,
                            weight: 'bold',
                            family: 'Helvetica'
                        },
                        padding: {
                            top: 10,
                            bottom: 30
                        }
                    },
                    legend: { display: false },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(255, 255, 255, 0.9)', // Clean white glass look
                        titleColor: '#333',
                        bodyColor: '#666',
                        borderColor: '#ddd',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 10,
                        displayColors: true, // Shows the little color box next to the value
                        callbacks: {
                            // This adds your unit (e.g., "%") to the value in the popup
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y + unit;
                                }
                                return label;
                            }
                        }
                    },
                    // The Health Line annotation
                    annotation: {
                        annotations: hasThreshold
                            ? {
                                healthLine: {
                                    type: 'line',
                                    yMin: threshold,
                                    yMax: threshold,
                                    borderColor: 'rgba(255, 99, 132, 0.6)',
                                    borderWidth: 1,
                                    borderDash: [5, 5],
                                    label: {
                                        display: true,
                                        content: 'Baseline',
                                        position: 'end',
                                        backgroundColor:
                                            'rgba(255, 99, 132, 0.7)',
                                        font: { size: 10 }
                                    }
                                }
                            }
                            : {}
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { maxTicksLimit: 8, color: '#999' }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#999' }
                    }
                }
            }
        });
    }
}