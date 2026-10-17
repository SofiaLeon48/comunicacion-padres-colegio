// Carga diferida de la librería DataTables (jQuery + Bootstrap 5 + Responsive).
import 'datatables.net-bs5/css/dataTables.bootstrap5.css';
import 'datatables.net-responsive-bs5/css/responsive.bootstrap5.css';

let promesa = null;

export function cargarDataTables() {
	promesa ??= (async () => {
		const { default: DataTable } = await import('datatables.net-bs5');
		await import('datatables.net-responsive-bs5');
		return DataTable;
	})();
	return promesa;
}

export const IDIOMA_ES = {
	decimal: ',',
	thousands: '.',
	emptyTable: 'No hay registros para mostrar',
	info: 'Mostrando _START_ a _END_ de _TOTAL_ registros',
	infoEmpty: 'Mostrando 0 registros',
	infoFiltered: '(filtrado de _MAX_ en total)',
	lengthMenu: 'Mostrar _MENU_',
	loadingRecords: 'Cargando...',
	processing: 'Procesando...',
	search: '',
	searchPlaceholder: 'Buscar...',
	zeroRecords: 'No se encontraron coincidencias',
	paginate: { first: '«', last: '»', next: '›', previous: '‹' },
	aria: { orderable: 'Ordenar por esta columna', orderableReverse: 'Orden inverso' }
};
