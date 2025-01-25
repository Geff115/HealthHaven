// appointment.js

// Constants
const API_BASE_URL = '/api/v1';
const ITEMS_PER_PAGE = 10;
let currentPage = 1;
let totalAppointments = 0;
let isLoading = false;

// State
let currentUserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

// Initialize the page
document.addEventListener('DOMContentLoaded', async () => {
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
        if (currentPage * ITEMS_PER_PAGE < totalAppointments) {
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
        if (!response.ok) throw new Error('Failed to fetch doctors');
        
        const doctors = await response.json();
        const select = document.getElementById('doctorSelect');
        
        doctors.forEach(doctor => {
            const option = document.createElement('option');
            option.value = doctor.id;
            option.textContent = `Dr. ${doctor.first_name} ${doctor.last_name} - ${doctor.specialization}`;
            select.appendChild(option);
        });
    } catch (error) {
        showNotification('Failed to load doctors list', 'error');
    }
}

// Load appointments with filters
async function loadAppointments() {
    if (isLoading) return; // Prevent duplicate calls
    isLoading = true;

    try {
        // Show loading spinner
        document.getElementById('loadingSpinner').classList.remove('hidden');

        const status = document.getElementById('statusFilter').value;
        const date = document.getElementById('dateFilter').value;

        const queryParams = new URLSearchParams({
            limit: ITEMS_PER_PAGE,
            offset: (currentPage - 1) * ITEMS_PER_PAGE
        });

        if (status) queryParams.append('status', status);
        if (date) queryParams.append('start_date', date);

        const response = await fetch(`${API_BASE_URL}/appointments?${queryParams}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to load appointments');
        }

        const data = await response.json();
        totalAppointments = data.total;
        renderAppointments(data.appointments);
        updatePagination();
    } catch (error) {
        showNotification(error.message, 'error');
    } finally {
        // Hide loading spinner and reset loading state
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
                Dr. ${appointment.doctor.last_name}
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
        const response = await fetch(`${API_BASE_URL}/appointments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(appointmentData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to book appointment');
        }
        
        showNotification('Appointment booked successfully!', 'success');
        event.target.reset();
        await loadAppointments();
        
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

// Cancel appointment
async function cancelAppointment(appointmentId) {
    if (!confirm('Are you sure you want to cancel this appointment?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/appointments/${appointmentId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to cancel appointment');
        
        showNotification('Appointment cancelled successfully', 'success');
        await loadAppointments();
        
    } catch (error) {
        showNotification('Failed to cancel appointment', 'error');
    }
}

// View appointment details
async function viewAppointment(appointmentId) {
    try {
        const response = await fetch(`${API_BASE_URL}/appointments/${appointmentId}?user_timezone=${currentUserTimezone}`);
        if (!response.ok) throw new Error('Failed to fetch appointment details');
        
        const appointment = await response.json();
        const detailsDiv = document.getElementById('appointmentDetails');
        detailsDiv.innerHTML = `
            <p><strong>Date & Time:</strong> ${formatDateTime(appointment.appointment_date, appointment.appointment_time)}</p>
            <p><strong>Doctor:</strong> Dr. ${appointment.doctor.last_name}, ${appointment.doctor.specialization}</p>
            <p><strong>Notes:</strong> ${appointment.appointment_note || 'None'}</p>
            <p><strong>Status:</strong> ${appointment.status}</p>
        `;
        // Display modal or expand the details section
        document.getElementById('detailsModal').classList.remove('hidden');
    } catch (error) {
        showNotification('Failed to load appointment details', 'error');
    }
}

// Close modal
function closeDetailsModal() {
    document.getElementById('detailsModal').classList.add('hidden');
}

// Delete appointment
async function deleteAppointment() {
    const appointmentId = document.getElementById('appointmentDetails').dataset.appointmentId;
    
    if (!confirm('Are you sure you want to delete this appointment? This action cannot be undone.')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/appointments/${appointmentId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to delete appointment');
        
        showNotification('Appointment deleted successfully', 'success');
        closeDetailsModal();
        await loadAppointments();
        
    } catch (error) {
        showNotification('Failed to delete appointment', 'error');
    }
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
    switch (status) {
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

function updatePagination() {
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');
    
    prevButton.disabled = currentPage === 1;
    nextButton.disabled = currentPage * ITEMS_PER_PAGE >= totalAppointments;
    
    document.getElementById('currentPage').textContent = currentPage;
}

function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `notification ${type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'} p-4 mb-4 rounded shadow`;
    notification.textContent = message;

    const notificationContainer = document.getElementById('notifications');
    notificationContainer.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, duration);
}