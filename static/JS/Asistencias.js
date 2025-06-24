document.addEventListener('DOMContentLoaded', fetchCourseAttendance);

async function fetchCourseAttendance() {
    try {
        const response = await fetch('/api/Asistencias');
        console.log(response)
        const courseData = await response.json(); 
        console.log(courseData)
        renderCourseAttendanceTable(courseData);
    } catch (error) {
        console.error('Error al cargar las asistencias por curso:', error);
        const tableBody = document.querySelector('#courseAttendanceTable tbody');
        tableBody.innerHTML = '<tr><td colspan="2">Error al cargar los datos.</td></tr>';
    }
}

function renderCourseAttendanceTable(courseData) {
    const tableBody = document.querySelector('#courseAttendanceTable tbody');
    tableBody.innerHTML = ''; // Limpiar tabla antes de renderizar

    if (Object.keys(courseData).length === 0) {
        tableBody.innerHTML = '<tr><td colspan="2">No hay asistencias registradas para ningún curso.</td></tr>';
        return;
    }

    for (const courseName in courseData) {
        if (courseData.hasOwnProperty(courseName)) {
            const totalAttendances = courseData[courseName];
            const row = tableBody.insertRow();
            row.insertCell().textContent = courseName;
            row.insertCell().textContent = totalAttendances;
        }
    }
}