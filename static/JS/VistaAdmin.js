document.addEventListener('DOMContentLoaded', fetchStudents);

async function fetchStudents() {
    try {
        const response = await fetch('/api/alumnos');
        console.log(response)

        const students = await response.json();
        console.log(students)
        renderStudentsTable(students);
    } catch (error) {
        console.error('Error al cargar alumnos:', error);
    }
}

function renderStudentsTable(students) {
    const tableBody = document.querySelector('#studentsTable tbody');
    tableBody.innerHTML = ''; 

    students.forEach(student => {
        const row = tableBody.insertRow();
        row.insertCell().textContent = student['Id'];
        row.insertCell().textContent = student['Documento'];
        // Asegúrate de manejar los casos donde ApellidoM o ApellidoP pueden ser null
        row.insertCell().textContent = `${student['Nombre'] || ''} ${student['ApellidoM'] || ''} ${student['ApellidoP'] || ''}`.trim();
        row.insertCell().textContent = student['Mail'] || '';
        row.insertCell().textContent = student['Teléfono'] || '';
        row.insertCell().textContent = student['Asistencia'] || 0; // Mostrar 0 si es null/undefined

        const actionsCell = row.insertCell();
        actionsCell.classList.add('action-buttons');
        const editButton = document.createElement('button');
        editButton.textContent = 'Editar';
        editButton.classList.add('edit-button');
        editButton.onclick = () => openEditModal(student);
        actionsCell.appendChild(editButton);
    });
}

function filterStudents() {
    const searchRut = document.getElementById('searchRut').value.trim();
    if (searchRut) {
        fetch(`/api/alumnos?rut=${encodeURIComponent(searchRut)}`)
            .then(response => response.json())
            .then(students => renderStudentsTable(students))
            .catch(error => console.error('Error al filtrar alumnos:', error));
    } else {
        fetchStudents(); 
    }
}

let currentEditingStudent = null; 

function openEditModal(student) {
    currentEditingStudent = student;
    document.getElementById('editId').value = student['Id'];
    document.getElementById('editTipoDocumento').value = student['Tipo documento'] || '';
    document.getElementById('editDocumento').value = student['Documento'] || '';
    document.getElementById('editNombre').value = student['Nombre'] || '';
    document.getElementById('editApellidoM').value = student['ApellidoM'] || '';
    document.getElementById('editApellidoP').value = student['ApellidoP'] || '';
    document.getElementById('editMail').value = student['Mail'] || '';
    document.getElementById('editTelefono').value = student['Teléfono'] || '';
    document.getElementById('editProducto').value = student['Producto'] || '';
    document.getElementById('editRutEmpresa').value = student['RutEmpresa'] || '';
    document.getElementById('editAsistencia').value = student['Asistencia'] || 0; // Asegura que sea un número
    document.getElementById('editNota').value = student['Nota'] || '';
    
    // --- CAMBIO CLAVE AQUÍ ---
    const fechaDeCursoInput = document.getElementById('editFechaDeCurso');
    if (student['FechaDeCurso']) {
        // Si el backend envía 'YYYY-MM-DD', se asigna directamente.
        fechaDeCursoInput.value = student['FechaDeCurso']; 
    } else {
        // Si es null o vacío, se limpia el campo.
        fechaDeCursoInput.value = ''; 
    }
    // --- FIN CAMBIO CLAVE ---
    
    document.getElementById('editSolicitud').value = student['Solicitud'] || '';
    document.getElementById('editNOp').value = student['N° OP'] || '';

    document.getElementById('editModal').style.display = 'flex'; 
}

function closeModal() {
    document.getElementById('editModal').style.display = 'none'; 
    currentEditingStudent = null;
}

document.getElementById('editForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const studentId = document.getElementById('editId').value;
    const updatedData = {};
    const inputs = this.querySelectorAll('input');
    inputs.forEach(input => {
        if (input.name) {
            // Asegurarse de que el campo de fecha se envíe como cadena vacía si está vacío
            if (input.name === 'FechaDeCurso' && input.value === '') {
                updatedData[input.name] = null; // O undefined, o manejarlo en el backend si prefieres cadena vacía
            } else {
                updatedData[input.name] = input.value;
            }
        }
    });

    // Convertir Asistencia a número antes de enviar
    updatedData['Asistencia'] = parseInt(updatedData['Asistencia'], 10);
    // Eliminar 'Id' del objeto enviado, ya que es parte de la URL
    delete updatedData['Id']; 

    try {
        const response = await fetch(`/api/alumnos/${studentId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatedData)
        });

        if (response.ok) {
            // Reemplazando alert() con un mensaje en la UI
            showMessageBox('Alumno actualizado con éxito.', 'success');
            closeModal();
            fetchStudents(); 
        } else {
            const errorData = await response.json();
            // Reemplazando alert() con un mensaje en la UI
            showMessageBox('Error al actualizar alumno: ' + (errorData.error || 'Error desconocido.'), 'error');
        }
    } catch (error) {
        console.error('Error al actualizar:', error);
        // Reemplazando alert() con un mensaje en la UI
        showMessageBox('No se pudo conectar con el servidor para actualizar el alumno.', 'error');
    }
});


window.onclick = function(event) {
    const modal = document.getElementById('editModal');
    if (event.target == modal) {
        closeModal();
    }
}

// Función para mostrar mensajes personalizados (reemplazo de alert)
function showMessageBox(message, type = 'info') {
    let messageBox = document.getElementById('messageBox');
    if (!messageBox) {
        messageBox = document.createElement('div');
        messageBox.id = 'messageBox';
        document.body.appendChild(messageBox);
        
        // Estilos básicos para el messageBox
        messageBox.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 15px 25px;
            border-radius: 8px;
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            color: white;
            z-index: 1000;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            display: none; /* Oculto por defecto */
            text-align: center;
        `;
    }

    messageBox.textContent = message;
    messageBox.style.display = 'block';

    if (type === 'success') {
        messageBox.style.backgroundColor = '#4CAF50'; // Verde
    } else if (type === 'error') {
        messageBox.style.backgroundColor = '#f44336'; // Rojo
    } else {
        messageBox.style.backgroundColor = '#2196F3'; // Azul (info)
    }

    // Ocultar el mensaje después de 3 segundos
    setTimeout(() => {
        messageBox.style.display = 'none';
    }, 3000);
}
