document.addEventListener('DOMContentLoaded', function () {
    // Get the canvas element for the chart
    const ctx = document.getElementById('expenseChart').getContext('2d');

    // Data passed from the template (via data attributes or inline script)
    const expenseData = JSON.parse(document.getElementById('expense-data').textContent);

    // Initialize Chart.js bar chart
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: expenseData.map(item => item.category),
            datasets: [{
                label: 'Expenses by Category ($)',
                data: expenseData.map(item => item.total),
                backgroundColor: ['#3B82F6', '#EF4444', '#FBBF24', '#10B981'],
                borderColor: ['#2563EB', '#DC2626', '#D97706', '#059669'],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Amount ($)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Category'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });
});