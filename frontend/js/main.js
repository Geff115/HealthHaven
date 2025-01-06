document.getElementById('bookingForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const location = document.getElementById('location').value;
    const time = document.getElementById('time').value;
    const doctor = document.getElementById('doctor').value;

    if (location && time && doctor) {
        alert('Appointment booked successfully!');
        this.reset();
    } else {
        alert('Please fill all fields');
    }
});