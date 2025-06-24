document.getElementById('attendanceForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const rutInput = document.getElementById('rut');
    const rut = rutInput.value.trim();
    const messageElement = document.getElementById('message');

    // Validación básica del rut
    if (validarRut(rut)) {
        console.log(rut)
        messageElement.textContent = 'RUT inválido. Por favor, ingrese un RUT chileno válido (Ej: 12.345.678-9).';
        messageElement.classList.remove('success');
        messageElement.classList.add('error');
        return;
    }

    try {
        const response = await fetch('/register_attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ rut: rut })
        });

        const data = await response.json();

        if (response.ok) {
            window.location.href = `/RegistroExitoso?nombre=${encodeURIComponent(data.nombre)}&fecha=${encodeURIComponent(data.fecha)}&hora=${encodeURIComponent(data.hora)}`;
        } else {
            messageElement.textContent = data.error || 'Ocurrió un error al registrar la asistencia.';
            messageElement.classList.remove('success');
            messageElement.classList.add('error');
        }
    } catch (error) {
        console.error('Error:', error);
        messageElement.textContent = 'No se pudo conectar con el servidor.';
        messageElement.classList.remove('success');
        messageElement.classList.add('error');
    }
});

//validar que sea chileno
function validarRut(rut) {
    if (!/^[0-9]+-[0-9kK]$/.test(rut)) {
        return false;
    }

    const [num, dv] = rut.split('-');
    const cuerpo = parseInt(num.replace(/\./g, ''), 10);
    let suma = 0;
    let multiplo = 2;

    for (let i = cuerpo.toString().length - 1; i >= 0; i--) {
        suma += parseInt(cuerpo.toString()[i], 10) * multiplo;
        multiplo = multiplo < 7 ? multiplo + 1 : 2;
    }

    const dvEsperado = 11 - (suma % 11);
    const dvCalculado = dvEsperado === 11 ? '0' : (dvEsperado === 10 ? 'K' : dvEsperado.toString());

    return dvCalculado.toLowerCase() === dv.toLowerCase();
}