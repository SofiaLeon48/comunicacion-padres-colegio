// Guardar archivos descargados (PDF / Excel).
// En el navegador se descarga normal; en la app móvil (Capacitor) el WebView no puede
// descargar, así que se guarda en el teléfono y se abre el menú "Compartir / Abrir con".
import { Capacitor } from '@capacitor/core';

function aBase64(blob) {
	return new Promise((ok, falla) => {
		const lector = new FileReader();
		lector.onload = () => ok(String(lector.result).split(',')[1]);
		lector.onerror = falla;
		lector.readAsDataURL(blob);
	});
}

export async function guardarArchivo(blob, nombre) {
	if (Capacitor.isNativePlatform()) {
		const { Filesystem, Directory } = await import('@capacitor/filesystem');
		const { Share } = await import('@capacitor/share');
		const archivo = await Filesystem.writeFile({ path: nombre, data: await aBase64(blob), directory: Directory.Cache });
		await Share.share({ title: nombre, files: [archivo.uri], dialogTitle: 'Guardar o abrir el reporte' });
		return;
	}
	const url = URL.createObjectURL(blob);
	const a = Object.assign(document.createElement('a'), { href: url, download: nombre });
	document.body.appendChild(a);
	a.click();
	a.remove();
	setTimeout(() => URL.revokeObjectURL(url), 2000);
}

export const esAppMovil = () => Capacitor.isNativePlatform();
