// script.js

const calendarGrid = document.querySelector('.calendar-grid');
const monthYear = document.getElementById('month-year');
const prevButton = document.getElementById('prev');
const nextButton = document.getElementById('next');
const bookingForm = document.getElementById('booking-form');
const selectedDateText = document.getElementById('selected-date');
const appointmentForm = document.getElementById('appointment-form');
let selectedDate = null;

let currentMonth = new Date().getMonth(); // Current month
let currentYear = new Date().getFullYear(); // Current year

// Function to render the calendar
function renderCalendar(month, year) {
    const firstDay = new Date(year, month).getDay();
    const lastDate = new Date(year, month + 1, 0).getDate();
    const days = [];

    // Set month and year display
    monthYear.textContent = `${getMonthName(month)} ${year}`;

    // Clear the previous calendar grid
    calendarGrid.innerHTML = '';

    // Empty spaces for the first days of the month
    for (let i = 0; i < firstDay; i++) {
        days.push('');
    }

    // Days of the current month
    for (let day = 1; day <= lastDate; day++) {
        days.push(day);
    }

    // Render the calendar grid
    days.forEach((day) => {
        const dayElement = document.createElement('div');
        if (day !== '') {
            dayElement.textContent = day;
            dayElement.addEventListener('click', () => selectDate(day));
        }
        calendarGrid.appendChild(dayElement);
    });
}

// Function to select a date
function selectDate(day) {
    const formattedDate = `${getMonthName(currentMonth)} ${day}, ${currentYear}`;
    selectedDate = new Date(currentYear, currentMonth, day);
    selectedDateText.textContent = `You selected: ${formattedDate}`;
    bookingForm.classList.remove('hidden');
}

// Function to get month name
function getMonthName(monthIndex) {
    const months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return months[monthIndex];
}

// Function to handle form submission
appointmentForm.addEventListener('submit', function(event) {
    event.preventDefault();
    alert('Appointment booked successfully!');
    appointmentForm.reset();
    bookingForm.classList.add('hidden');
    selectedDate = null;
});

// Event listeners for navigation buttons
prevButton.addEventListener('click', () => {
    currentMonth--;
    if (currentMonth < 0) {
        currentMonth = 11;
        currentYear--;
    }
    renderCalendar(currentMonth, currentYear);
});

nextButton.addEventListener('click', () => {
    currentMonth++;
    if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
    }
    renderCalendar(currentMonth, currentYear);
});

// Initial render of the calendar
renderCalendar(currentMonth, currentYear);

// Function to generate time slots
function generateTimeSlots() {
  const timeSlotDropdown = document.getElementById('time-slot');
  timeSlotDropdown.innerHTML = ''; // Clear existing options

  const slots = [];
  let startTime = new Date(selectedDate.setHours(0, 0, 0, 0)); // Start at 00:00
  const endTime = new Date(selectedDate.setHours(23, 59, 59, 999)); // End at 23:59

  while (startTime <= endTime) {
      const formattedTime = startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      slots.push(formattedTime);

      // Increment by 45 minutes
      startTime = new Date(startTime.getTime() + 45 * 60 * 1000);
  }

  // Populate the dropdown
  slots.forEach((slot) => {
      const option = document.createElement('option');
      option.value = slot;
      option.textContent = slot;
      timeSlotDropdown.appendChild(option);
  });
}

// Modify the selectDate function to include time slots generation
function selectDate(day) {
  const formattedDate = `${getMonthName(currentMonth)} ${day}, ${currentYear}`;
  selectedDate = new Date(currentYear, currentMonth, day);
  selectedDateText.textContent = `You selected: ${formattedDate}`;
  bookingForm.classList.remove('hidden');
  generateTimeSlots();
}

// Update form submission to include the selected time slot
appointmentForm.addEventListener('submit', function(event) {
  event.preventDefault();
  const selectedTime = document.getElementById('time-slot').value;
  const name = document.getElementById('name').value;
  const email = document.getElementById('email').value;

  if (selectedTime) {
      alert(`Appointment booked successfully for ${selectedDateText.textContent} at ${selectedTime}.\nName: ${name}\nEmail: ${email}`);
      appointmentForm.reset();
      bookingForm.classList.add('hidden');
      selectedDate = null;
  } else {
      alert('Please select a time slot.');
  }
});
