document.addEventListener('DOMContentLoaded', () => {
    const txtNombres = document.getElementById('txtNombres');
    const txtMotivo1 = document.getElementById('txtMotivo1');
    const txtEvento = document.getElementById('txtEvento');
    const txtMotivo2 = document.getElementById('txtMotivo2');
    const txtFecha = document.getElementById('txtFecha');
    const btnDownload = document.getElementById('btnDownload');
    const btnText = document.getElementById('btnText');
    const statusAlert = document.getElementById('statusAlert');
    const previewImg = document.getElementById('previewImg');
    const previewSpinner = document.getElementById('previewSpinner');

    let debounceTimer = null;

    function getFormData() {
        return {
            nombres: txtNombres.value,
            motivo1: txtMotivo1.value,
            evento: txtEvento.value,
            motivo2: txtMotivo2.value,
            fecha: txtFecha.value
        };
    }

    async function updatePreview() {
        previewSpinner.classList.remove('hidden');
        try {
            const res = await fetch('/api/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(getFormData())
            });

            if (!res.ok) throw new Error('Error al generar vista previa');

            const blob = await res.blob();
            const objectUrl = URL.createObjectURL(blob);
            previewImg.onload = () => {
                URL.revokeObjectURL(objectUrl);
                previewSpinner.classList.add('hidden');
            };
            previewImg.src = objectUrl;
        } catch (err) {
            console.error(err);
            previewSpinner.classList.add('hidden');
        }
    }

    function schedulePreview() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(updatePreview, 350);
    }

    [txtNombres, txtMotivo1, txtEvento, txtMotivo2, txtFecha].forEach(el => {
        el.addEventListener('input', schedulePreview);
    });

    // Descarga automática directa al generar
    btnDownload.addEventListener('click', async () => {
        const nombresList = txtNombres.value.trim();
        if (!nombresList) {
            showAlert('Por favor ingresa al menos un nombre.', 'error');
            return;
        }

        btnDownload.disabled = true;
        btnText.textContent = 'Procesando y generando lote PDF...';
        showAlert('Generando diplomas... la descarga comenzará automáticamente.', 'success');

        try {
            const res = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(getFormData())
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.error || 'Error al generar el lote.');
            }

            // Extraer nombre de archivo desde cabeceras Content-Disposition o predeterminado
            const disposition = res.headers.get('Content-Disposition');
            let filename = 'Reconocimientos_UniFreire.pdf';
            if (disposition && disposition.includes('filename=')) {
                const match = disposition.match(/filename="?([^";]+)"?/);
                if (match && match[1]) filename = match[1];
            }

            // Descarga automática directa
            const blob = await res.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click(); // Disparo automático de descarga
            window.URL.revokeObjectURL(downloadUrl);
            a.remove();

            showAlert(`✓ ¡Descarga completada con éxito! Archivo: ${filename}`, 'success');
        } catch (err) {
            console.error(err);
            showAlert(`Error: ${err.message}`, 'error');
        } finally {
            btnDownload.disabled = false;
            btnText.textContent = 'Generar y Descargar Reconocimientos (PDF)';
        }
    });

    function showAlert(msg, type) {
        statusAlert.textContent = msg;
        statusAlert.className = `status-alert ${type}`;
        statusAlert.classList.remove('hidden');
        if (type === 'success') {
            setTimeout(() => {
                statusAlert.classList.add('hidden');
            }, 6000);
        }
    }

    // Inicializar primera vista previa al cargar la página
    updatePreview();
});
