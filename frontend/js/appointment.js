// appointment.js

// Constants
const API_BASE_URL = '/api/v1/appointments';
const ITEMS_PER_PAGE = 10;
let currentPage = 1;
let totalAppointments = 0;
let isLoading = false;

// Get token from localStorage
let token = localStorage.getItem('token');

// State
let currentUserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

// Initialize the page
document.addEventListener('DOMContentLoaded', async () => {
    if (!token) {
        window.location.href = '/login.html';
        return;
    }

    // Initialize date/time pickers
    initializeDatePickers();
    
    // Load initial data
    await Promise.all([
        loadDoctors(),
        loadAppointments()
    ]);

    // Set up event listeners
    setupEventListeners();
});

// Initialize Flatpickr date/time pickers
function initializeDatePickers() {
    // Appointment date picker
    flatpickr("#appointmentDate", {
        minDate: "today",
        dateFormat: "Y-m-d"
    });

    // Appointment time picker
    flatpickr("#appointmentTime", {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
        minTime: "09:00",
        maxTime: "17:00",
        minuteIncrement: 30
    });

    // Filter date picker
    flatpickr("#dateFilter", {
        dateFormat: "Y-m-d",
        onChange: () => loadAppointments()
    });
}

// Set up event listeners
function setupEventListeners() {
    // Form submission
    document.getElementById('appointmentForm').addEventListener('submit', handleAppointmentSubmit);
    
    // Filters
    document.getElementById('statusFilter').addEventListener('change', () => loadAppointments());
    
    // Pagination
    document.getElementById('prevPage').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadAppointments();
        }
    });
    
    document.getElementById('nextPage').addEventListener('click', () => {
        const maxPage = Math.ceil(totalAppointments / ITEMS_PER_PAGE);
        if (currentPage < maxPage) {
            currentPage++;
            loadAppointments();
        }
    });
}

// Load doctors for the select dropdown
async function loadDoctors() {
    try {
        const response = await fetch(`${API_BASE_URL}/doctors`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to fetch doctors');
        }
        
        const doctors = await response.json();
        const select = document.getElementById('doctorSelect');
        
        select.innerHTML = '<option value="">Choose a doctor...</option>';
        
        doctors.forEach(doctor => {
            const option = document.createElement('option');
            option.value = doctor.id;
            option.textContent = `Dr. ${doctor.first_name} ${doctor.last_name} - ${doctor.specialization}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Doctor loading error:', error);
        showNotification(error.message || 'Failed to load doctors list', 'error');
    }
}

// Load appointments with filters
async function loadAppointments() {
    if (isLoading) return;

    try {
        isLoading = true;
        document.getElementById('loadingSpinner').classList.remove('hidden');

        const status = document.getElementById('statusFilter').value;
        const date = document.getElementById('dateFilter').value;
        const offset = (currentPage - 1) * ITEMS_PER_PAGE;

        const queryParams = new URLSearchParams({
            limit: ITEMS_PER_PAGE,
            offset: offset
        });

        if (status) queryParams.append('status', status);
        if (date) queryParams.append('start_date', date);

        const response = await fetch(`${API_BASE_URL}/list?${queryParams}`, {  // Updated endpoint
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to load appointments');
        }

        const data = await response.json();
        totalAppointments = data.total;
        renderAppointments(data.items);
        updatePagination();

    } catch (error) {
        showNotification(error.message, 'error');
    } finally {
        document.getElementById('loadingSpinner').classList.add('hidden');
        isLoading = false;
    }
}

// Render appointments to the table
function renderAppointments(appointments) {
    const tbody = document.getElementById('appointmentsList');
    tbody.innerHTML = '';
    
    appointments.forEach(appointment => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap">
                ${formatDateTime(appointment.appointment_date, appointment.appointment_time)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                Dr. ${appointment.doctor.last_name}, ${appointment.doctor.specialization}
            </td>
            <td class="px-6 py-4">
                ${appointment.appointment_note}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusClass(appointment.status)}">
                    ${appointment.status}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button onclick="viewAppointment(${appointment.id})" class="text-blue-600 hover:text-blue-900 mr-2">View</button>
                ${appointment.status === 'SCHEDULED' ? `
                    <button onclick="cancelAppointment(${appointment.id})" class="text-red-600 hover:text-red-900">Cancel</button>
                ` : ''}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Handle appointment form submission
async function handleAppointmentSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const appointmentData = {
        doctor_id: parseInt(formData.get('doctor_id')),
        appointment_date: formData.get('appointment_date'),
        appointment_time: formData.get('appointment_time'),
        appointment_note: formData.get('appointment_note'),
        user_timezone: currentUserTimezone
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(appointmentData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to book appointment');
        }
        
        showNotification('Appointment booked successfully!', 'success');
        event.target.reset();
        await loadAppointments();
        
    } catch (error) {
        showNotification(error.message, 'error');
        console.error('Appointment booking error:', error);
    }
}

// View appointment details
async function viewAppointment(appointmentId) {
    try {
        const response = await fetch(`${API_BASE_URL}/${appointmentId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch appointment details');
        }
        
        const appointment = await response.json();
        const detailsDiv = document.getElementById('appointmentDetails');
        detailsDiv.innerHTML = `
            <p><strong>Date & Time:</strong> ${formatDateTime(appointment.appointment_date, appointment.appointment_time)}</p>
            <p><strong>Doctor:</strong> Dr. ${appointment.doctor.last_name}, ${appointment.doctor.specialization}</p>
            <p><strong>Notes:</strong> ${appointment.appointment_note || 'None'}</p>
            <p><strong>Status:</strong> ${appointment.status}</p>
        `;
        
        document.getElementById('appointmentModal').classList.remove('hidden');
    } catch (error) {
        showNotification('Failed to load appointment details', 'error');
    }
}

// Cancel appointment
async function cancelAppointment(appointmentId) {
    if (!confirm('Are you sure you want to cancel this appointment?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/${appointmentId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to cancel appointment');
        }
        
        showNotification('Appointment cancelled successfully', 'success');
        await loadAppointments();
        
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

// Close modal
function closeDetailsModal() {
    document.getElementById('appointmentModal').classList.add('hidden');
}

// Format date and time for display
function formatDateTime(date, time) {
    const localDateTime = new Date(`${date}T${time}`);
    return localDateTime.toLocaleString('en-US', { 
        timeZone: currentUserTimezone, 
        dateStyle: 'medium', 
        timeStyle: 'short' 
    });
}

// Get class for appointment status
function getStatusClass(status) {
    switch (status.toUpperCase()) {
        case 'SCHEDULED':
            return 'bg-green-100 text-green-800';
        case 'CANCELLED':
            return 'bg-red-100 text-red-800';
        case 'COMPLETED':
            return 'bg-blue-100 text-blue-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

// Update pagination information
function updatePagination() {
    const startRange = (currentPage - 1) * ITEMS_PER_PAGE + 1;
    const endRange = Math.min(currentPage * ITEMS_PER_PAGE, totalAppointments);
    
    document.getElementById('startRange').textContent = startRange;
    document.getElementById('endRange').textContent = endRange;
    document.getElementById('totalAppointments').textContent = totalAppointments;
    
    // Update button states
    document.getElementById('prevPage').disabled = currentPage === 1;
    document.getElementById('nextPage').disabled = endRange >= totalAppointments;
}

// Show notification using Toastify
function showNotification(message, type = 'info') {
    Toastify({
        text: message,
        duration: 3000,
        gravity: "top",
        position: "right",
        style: {
            background: type === 'error' ? '#ef4444' : '#22c55e'
        }
    }).showToast();
}