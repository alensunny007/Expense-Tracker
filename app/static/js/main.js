
let chartInstance = null;
let dashboardInitialized = false;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard when page loads
    initializeDashboard();
});

// Cleanup chart when page is unloaded
window.addEventListener('beforeunload', function() {
    if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
    }
});

async function initializeDashboard() {
    if (dashboardInitialized) {
        console.log('Dashboard already initialized, skipping...');
        return;
    }
    
    dashboardInitialized = true;
    console.log('Initializing dashboard...');
    
    try {
        // Fetch dashboard data from API
        const response = await fetch('/api/dashboard-data');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load dashboard data');
        }
        
        // Update UI elements with fetched data
        updateDashboardStats(data);
        
        // Initialize chart with data
        initializeChart(data.expenses_by_category);
        
        console.log('Dashboard loaded successfully');
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showErrorMessage('Failed to load dashboard data. Please refresh the page.');
    }
}

function updateDashboardStats(data) {
    // Update total expenses display
    const totalExpensesElement = document.querySelector('.total-expenses');
    if (totalExpensesElement) {
        totalExpensesElement.textContent = `₹${data.total_expenses.toFixed(2)}`;
    }
    
    // Update category count
    const categoryCountElement = document.querySelector('.category-count');
    if (categoryCountElement) {
        categoryCountElement.textContent = data.category_count;
    }
    
    // Update this month display (same as total for now)
    const thisMonthElement = document.querySelector('.this-month');
    if (thisMonthElement) {
        thisMonthElement.textContent = `₹${data.total_expenses.toFixed(2)}`;
    }
}

 // Global variable to store chart instance

function initializeChart(categoryData) {
    const ctx = document.getElementById('expenseChart');
    
    if (!ctx) {
        console.error('Chart canvas not found');
        return;
    }
    
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded');
        showErrorMessage('Chart library not loaded. Please refresh the page.');
        return;
    }
    
    // Destroy existing chart if it exists
    if (chartInstance) {
        console.log('Destroying existing chart...');
        chartInstance.destroy();
        chartInstance = null;
    }
    
    // Prepare chart data
    const labels = [];
    const data = [];
    
    if (categoryData && categoryData.length > 0) {
        categoryData.forEach(function(item) {
            labels.push(item[0]); // category name
            data.push(item[1]);   // total amount
        });
        
        // Create the chart and store the instance
        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Expenses by Category (₹)',
                    data: data,
                    backgroundColor: [
                        'rgba(163, 230, 53, 0.8)',  // lime-400
                        'rgba(34, 197, 94, 0.8)',   // green-500
                        'rgba(59, 130, 246, 0.8)',  // blue-500
                        'rgba(236, 72, 153, 0.8)',  // pink-500
                        'rgba(245, 158, 11, 0.8)',  // amber-500
                        'rgba(139, 92, 246, 0.8)',  // violet-500
                        'rgba(239, 68, 68, 0.8)',   // red-500
                        'rgba(6, 182, 212, 0.8)',   // cyan-500
                        'rgba(168, 85, 247, 0.8)'   // purple-500
                    ],
                    borderColor: [
                        'rgb(163, 230, 53)',   // lime-400
                        'rgb(34, 197, 94)',    // green-500
                        'rgb(59, 130, 246)',   // blue-500
                        'rgb(236, 72, 153)',   // pink-500
                        'rgb(245, 158, 11)',   // amber-500
                        'rgb(139, 92, 246)',   // violet-500
                        'rgb(239, 68, 68)',    // red-500
                        'rgb(6, 182, 212)',    // cyan-500
                        'rgb(168, 85, 247)'    // purple-500
                    ],
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#D1D5DB', // gray-300
                            font: {
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.9)', // gray-900
                        titleColor: '#F9FAFB', // gray-50
                        bodyColor: '#F9FAFB',  // gray-50
                        borderColor: '#4B5563', // gray-600
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ₹${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { 
                            display: true, 
                            text: 'Amount (₹)',
                            color: '#D1D5DB', // gray-300
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            color: '#9CA3AF', // gray-400
                            font: {
                                size: 12
                            },
                            callback: function(value) {
                                return '₹' + value.toFixed(0);
                            }
                        },
                        grid: {
                            color: 'rgba(75, 85, 99, 0.3)' // gray-600 with opacity
                        }
                    },
                    x: {
                        title: { 
                            display: true, 
                            text: 'Category',
                            color: '#D1D5DB', // gray-300
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            color: '#9CA3AF', // gray-400
                            font: {
                                size: 12
                            }
                        },
                        grid: {
                            color: 'rgba(75, 85, 99, 0.3)' // gray-600 with opacity
                        }
                    }
                }
            }
        });
        
        console.log(`Chart created with ${categoryData.length} categories`);
        
    } else {
        // Show message when no data is available
        ctx.parentElement.innerHTML = `
            <div class="flex items-center justify-center h-96">
                <div class="text-center">
                    <svg class="w-16 h-16 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                    <p class="text-gray-400 text-lg">No expense data available</p>
                    <p class="text-gray-500 text-sm mt-2">Add some expenses to see your spending breakdown</p>
                </div>
            </div>
        `;
        console.log('No chart data available');
    }
}

function showErrorMessage(message) {
        if (!document.getElementById('expenseChart')) {
        return; // Not on dashboard page, don't show error
    }
    // Create or update error message element
    let errorElement = document.getElementById('dashboard-error');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.id = 'dashboard-error';
        errorElement.className = 'bg-red-600 text-white p-4 rounded-lg mb-6';
        
        // Insert at the top of the dashboard content
        const dashboardContent = document.querySelector('.max-w-7xl');
        if (dashboardContent) {
            dashboardContent.insertBefore(errorElement, dashboardContent.firstChild);
        }
    }
    
    errorElement.innerHTML = `
        <div class="flex items-center">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>${message}</span>
            <button onclick="location.reload()" class="ml-4 px-3 py-1 bg-red-700 rounded text-sm hover:bg-red-800">
                Retry
            </button>
        </div>
    `;
}