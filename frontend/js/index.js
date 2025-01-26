document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/homepage/homepage-data');
        if (response.ok) {
            const data = await response.json();
            populateHomepage(data);
        } else {
            console.error('Failed to fetch homepage data:', response.statusText);
        }
    } catch (error) {
        console.error('Error fetching homepage data:', error);
    }
});

function populateHomepage(data) {
    const locationSelect = document.getElementById('location-select');
    const specialtySelect = document.getElementById('specialty-select');

    data.locations.forEach(location => {
        const option = document.createElement('option');
        option.value = location.toLowerCase().replace(/ /g, '-');
        option.textContent = location;
        locationSelect.appendChild(option);
    });

    data.specialties.forEach(specialty => {
        const option = document.createElement('option');
        option.value = specialty.toLowerCase();
        option.textContent = specialty;
        specialtySelect.appendChild(option);
    });
}