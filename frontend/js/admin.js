function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Authorization': `Bearer ${token}`
    };
}

async function fetchWithAuth(url, options = {}) {
    const headers = {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
        ...options.headers
    };

    const response = await fetch(url, {
        ...options,
        headers
    });

    if (response.status === 401 || response.status === 403) {
        window.location.href = '/login.html';
        return null;
    }
    return response;
}

document.addEventListener('DOMContentLoaded', async function() {
    try {
        const response = await fetch('/admin.html', {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('Not authorized');
        }
    } catch (error) {
        console.error('Authorization failed:', error);
        window.location.href = '/login.html';
        return;
    }

    // Initialize the admin page
    refreshData();
});


let selectedRequestId = null;

// Fetch and display dashboard stats
async function fetchDashboardStats() {
    try {
        const response = await fetchWithAuth('/admin/dashboard');
        if (!response) return;
        const data = await response.json();
        
        document.getElementById('totalUsers').textContent = data.total_users;
        document.getElementById('pendingRequests').textContent = data.pending_doctor_requests;
        document.getElementById('totalDoctors').textContent = 
            data.role_summary?.DOCTOR || 0;
    } catch (error) {
        console.error('Error fetching dashboard stats:', error);
    }
}

// Fetch and display doctor requests
async function fetchDoctorRequests() {
    const searchQuery = document.getElementById('searchInput').value;
    const status = document.getElementById('statusFilter').value;
    const tableBody = document.getElementById('requestsTableBody');
    
    try {
        const response = await fetchWithAuth(
            `/admin/doctor-requests?status=${status}&search=${searchQuery}`
        );
        if (!response) return;
        const data = await response.json();
        
        tableBody.innerHTML = data.requests.map(request => `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${request.first_name} ${request.last_name}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">${request.email}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${new Date(request.created_at).toLocaleDateString()}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">${request.role}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${request.role === 'DOCTOR_PENDING' ? `
                        <button onclick="showApprovalModal(${request.id})" 
                                class="bg-green-500 text-white px-3 py-1 rounded-md mr-2 hover:bg-green-600">
                            Approve
                        </button>
                        <button onclick="showRejectionModal(${request.id})" 
                                class="bg-red-500 text-white px-3 py-1 rounded-md hover:bg-red-600">
                            Reject
                        </button>
                    ` : '-'}
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error fetching doctor requests:', error);
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-red-500">
                    Error loading doctor requests
                </td>
            </tr>
        `;
    }
}

// Modal functions
function showRejectionModal(requestId) {
    selectedRequestId = requestId;
    document.getElementById('rejectionModal').classList.remove('hidden');
}

function closeRejectionModal() {
    document.getElementById('rejectionModal').classList.add('hidden');
    document.getElementById('rejectionReason').value = '';
    selectedRequestId = null;
}

function showApprovalModal(requestId) {
    selectedRequestId = requestId;
    document.getElementById('approvalModal').classList.remove('hidden');
}

function closeApprovalModal() {
    document.getElementById('approvalModal').classList.add('hidden');
    selectedRequestId = null;
}

// Handle request approval
async function confirmApprove() {
    if (!selectedRequestId) return;
    
    try {
        const response = await fetchWithAuth(
            `/admin/doctor-requests/${selectedRequestId}/approve`,
            {
                method: 'PUT'
            }
        );
        if (!response) return;
        
        if (response.ok) {
            closeApprovalModal();
            await refreshData();
        } else {
            throw new Error('Failed to approve request');
        }
    } catch (error) {
        console.error('Error approving request:', error);
        alert('Failed to approve doctor request');
    }
}

// Handle request rejection
async function confirmReject() {
    if (!selectedRequestId) return;
    
    const reason = document.getElementById('rejectionReason').value;
    if (reason.length < 10) {
        alert('Rejection reason must be at least 10 characters');
        return;
    }
    
    try {
        const response = await fetchWithAuth(
            `/admin/doctor-requests/${selectedRequestId}/reject`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rejection_reason: reason })
            }
        );
        if (!response) return;
        
        if (response.ok) {
            closeRejectionModal();
            await refreshData();
        } else {
            throw new Error('Failed to reject request');
        }
    } catch (error) {
        console.error('Error rejecting request:', error);
        alert('Failed to reject doctor request');
    }
}

// Refresh all data
async function refreshData() {
    await Promise.all([
        fetchDashboardStats(),
        fetchDoctorRequests()
    ]);
}

// Event listeners
document.getElementById('searchInput').addEventListener('input', debounce(fetchDoctorRequests, 300));
document.getElementById('statusFilter').addEventListener('change', fetchDoctorRequests);

// Debounce helper function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

document.getElementById('logout-btn').addEventListener('click', () => {
    localStorage.clear();
    sessionStorage.clear();
    window.location.replace('/login.html');
});