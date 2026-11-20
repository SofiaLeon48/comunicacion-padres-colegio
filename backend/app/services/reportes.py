"""
Módulo Reporte: arma los reportes y los exporta en PDF (reportlab) o Excel (openpyxl).

Cada reporte:
  - cruza al menos 3 tablas relacionadas;
  - NO muestra ningún ID (solo nombres, fechas y valores legibles);
  - se filtra por rango de fechas, grupo y estado / prioridad;
  - sale con formato institucional: encabezado, pie de página, tipografía y colores.
"""
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO

from fastapi import HTTPException

from app.core.config import ahora_local
from app.repositories.reporte_repo import ReporteRepository

AZUL = "#1E3A8A"
AZUL_CLARO = "#E8EEFB"
GRIS = "#64748B"
NOMBRE_APP = "Conecta Escolar"
INSTITUCION = "Institución Educativa · Comunicación padres-colegio"

repo = ReporteRepository()


@dataclass
class Columna:
    clave: str
    titulo: str
    tipo: str = "texto"      # texto | fechahora | numero | porcentaje
    ancho: float = 1.0       # ancho relativo


TIPOS = {
    "comunicados": {
        "titulo": "Reporte de lectura de comunicados",
        "tablas": "comunicados, grupos, usuarios, confirmaciones de lectura y acudientes",
        "estado_nombre": "Prioridad",
        "estados": ["normal", "urgente"],
        "columnas": [
            Columna("fecha", "Publicado", "fechahora", 1.35), Columna("titulo", "Comunicado", "texto", 2.6),
            Columna("grupo", "Dirigido a", "texto", 1.1), Columna("autor", "Publicado por", "texto", 1.5),
            Columna("prioridad", "Prioridad", "texto", 0.8), Columna("destinatarios", "Destinatarios", "numero", 0.9),
            Columna("confirmados", "Confirmaron", "numero", 0.9), Columna("lectura", "% lectura", "porcentaje", 0.8),
        ],
    },
    "citaciones": {
        "titulo": "Reporte de citaciones a acudientes",
        "tablas": "citaciones, estudiantes, grupos, usuarios (docentes y acudientes) y asistencia",
        "estado_nombre": "Estado",
        "estados": ["pendiente", "confirmada", "realizada", "cancelada"],
        "columnas": [
            Columna("fecha", "Fecha y hora", "fechahora", 1.35), Columna("estudiante", "Estudiante", "texto", 1.5),
            Columna("grupo", "Grupo", "texto", 0.6), Columna("docente", "Docente", "texto", 1.3),
            Columna("acudiente", "Acudiente", "texto", 1.3), Columna("motivo", "Motivo", "texto", 2.2),
            Columna("lugar", "Lugar", "texto", 1.0), Columna("estado", "Estado", "texto", 0.8),
            Columna("asistencia", "Asistencia", "texto", 0.9),
        ],
    },
}


def fmt_fecha(v) -> str:
    if isinstance(v, datetime):
        return v.strftime("%d/%m/%Y %I:%M %p").replace("AM", "a. m.").replace("PM", "p. m.")
    if isinstance(v, date):
        return v.strftime("%d/%m/%Y")
    return str(v) if v is not None else ""


def texto_celda(col: Columna, v) -> str:
    if v is None:
        return "No aplica" if col.tipo == "porcentaje" else "—"
    if col.tipo == "fechahora":
        return fmt_fecha(v)
    if col.tipo == "porcentaje":
        return f"{float(v):.1f} %".replace(".", ",")
    return str(v)


def construir(tipo: str, desde: date | None, hasta: date | None, grupo_id: int | None, estado: str | None) -> dict:
    """Consulta los datos y arma el reporte (columnas, filas, criterios y resumen)."""
    if tipo not in TIPOS:
        raise HTTPException(status_code=422, detail="Tipo de reporte no válido.")
    if desde and hasta and desde > hasta:
        raise HTTPException(status_code=422, detail="La fecha inicial no puede ser posterior a la final.")
    defi = TIPOS[tipo]
    if estado and estado not in defi["estados"]:
        raise HTTPException(status_code=422, detail=f"{defi['estado_nombre']} no válido(a).")

    if tipo == "comunicados":
        filas = repo.reporte_comunicados(desde, hasta, grupo_id, estado)
        con_lectura = [float(f["lectura"]) for f in filas if f["lectura"] is not None]
        resumen = {
            "Comunicados": len(filas),
            "Urgentes": sum(1 for f in filas if f["prioridad"] == "Urgente"),
            "Lectura promedio": f"{(sum(con_lectura) / len(con_lectura)) if con_lectura else 0:.1f} %".replace(".", ","),
            "Confirmaciones": sum(int(f["confirmados"]) for f in filas),
        }
    else:
        filas = repo.reporte_citaciones(desde, hasta, grupo_id, estado)
        registradas = [f for f in filas if f["asistencia"] != "Sin registrar"]
        asistio = sum(1 for f in registradas if f["asistencia"] == "Asistió")
        resumen = {
            "Citaciones": len(filas),
            "Realizadas": sum(1 for f in filas if f["estado"] == "Realizada"),
            "Canceladas": sum(1 for f in filas if f["estado"] == "Cancelada"),
            "Asistencia": f"{(100 * asistio / len(registradas)) if registradas else 0:.1f} %".replace(".", ","),
        }

    grupo = (repo.nombre_grupo(grupo_id) if grupo_id else None) or "Todos"
    criterios = {
        "Periodo": f"{fmt_fecha(desde) if desde else 'Desde el inicio'} – {fmt_fecha(hasta) if hasta else 'hoy'}",
        "Grupo": grupo,
        defi["estado_nombre"]: estado.capitalize() if estado else "Todos",
    }
    return {
        "tipo": tipo, "titulo": defi["titulo"], "tablas": defi["tablas"],
        "columnas": [{"clave": c.clave, "titulo": c.titulo, "tipo": c.tipo} for c in defi["columnas"]],
        "filas": filas, "criterios": criterios, "resumen": resumen,
    }


def texto_criterios(rep: dict) -> str:
    return " · ".join(f"{k}: {v}" for k, v in rep["criterios"].items())


def nombre_archivo(rep: dict, extension: str) -> str:
    return f"{rep['tipo']}_{ahora_local():%Y%m%d_%H%M}.{extension}"


# ----------------------------------------------------------------------------- PDF
def generar_pdf(rep: dict, generado_por: str, analisis: str | None = None) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    azul, azul_claro, gris = colors.HexColor(AZUL), colors.HexColor(AZUL_CLARO), colors.HexColor(GRIS)
    generado = ahora_local()
    ancho_pag, alto_pag = landscape(A4)

    class CanvasNumerado(rl_canvas.Canvas):
        """Dibuja encabezado y pie en cada página, con 'Página X de Y'."""
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._paginas = []

        def showPage(self):
            self._paginas.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._paginas)
            for estado in self._paginas:
                self.__dict__.update(estado)
                self._decorar(total)
                super().showPage()
            super().save()

        def _decorar(self, total):
            # Encabezado: franja azul con el nombre de la plataforma y el título del reporte
            self.setFillColor(azul)
            self.rect(0, alto_pag - 2.2 * cm, ancho_pag, 2.2 * cm, stroke=0, fill=1)
            self.setFillColor(colors.HexColor("#3B82F6"))
            self.rect(0, alto_pag - 2.35 * cm, ancho_pag, 0.15 * cm, stroke=0, fill=1)
            self.setFillColor(colors.white)
            self.circle(1.9 * cm, alto_pag - 1.1 * cm, 0.55 * cm, stroke=0, fill=1)
            self.setFillColor(azul)
            self.setFont("Helvetica-Bold", 13)
            self.drawCentredString(1.9 * cm, alto_pag - 1.32 * cm, "CE")
            self.setFillColor(colors.white)
            self.setFont("Helvetica-Bold", 15)
            self.drawString(2.8 * cm, alto_pag - 1.0 * cm, NOMBRE_APP)
            self.setFont("Helvetica", 9)
            self.drawString(2.8 * cm, alto_pag - 1.55 * cm, INSTITUCION)
            self.setFont("Helvetica-Bold", 11)
            self.drawRightString(ancho_pag - 1.5 * cm, alto_pag - 1.0 * cm, rep["titulo"])
            self.setFont("Helvetica", 9)
            self.drawRightString(ancho_pag - 1.5 * cm, alto_pag - 1.55 * cm, f"Generado el {fmt_fecha(generado)}")
            # Pie de página
            self.setStrokeColor(azul)
            self.setLineWidth(0.8)
            self.line(1.5 * cm, 1.3 * cm, ancho_pag - 1.5 * cm, 1.3 * cm)
            self.setFillColor(gris)
            self.setFont("Helvetica", 8)
            self.drawString(1.5 * cm, 0.85 * cm, f"{NOMBRE_APP} · Generado por {generado_por} · Documento informativo de uso institucional")
            self.drawRightString(ancho_pag - 1.5 * cm, 0.85 * cm, f"Página {self._pageNumber} de {total}")

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=3.0 * cm, bottomMargin=1.8 * cm, title=rep["titulo"], author=NOMBRE_APP)
    estilo_titulo = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=azul, spaceAfter=2)
    estilo_sub = ParagraphStyle("s", fontName="Helvetica", fontSize=9, textColor=gris, spaceAfter=8)
    estilo_celda = ParagraphStyle("c", fontName="Helvetica", fontSize=8, leading=10)
    estilo_cab = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.white)
    estilo_kpi_v = ParagraphStyle("kv", fontName="Helvetica-Bold", fontSize=15, textColor=azul, alignment=TA_CENTER)
    estilo_kpi_t = ParagraphStyle("kt", fontName="Helvetica", fontSize=8, textColor=gris, alignment=TA_CENTER)
    estilo_ia = ParagraphStyle("ia", fontName="Helvetica", fontSize=9, leading=12)
    util = ancho_pag - 3 * cm
    e = []

    e.append(Paragraph(rep["titulo"], estilo_titulo))
    e.append(Paragraph(f"Fuente: {rep['tablas']}.", estilo_sub))

    # Criterios aplicados
    crit = Table([[Paragraph(f"<b>{k}:</b> {v}", estilo_celda) for k, v in rep["criterios"].items()]],
                 colWidths=[util / len(rep["criterios"])] * len(rep["criterios"]))
    crit.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), azul_claro), ("BOX", (0, 0), (-1, -1), 0.5, azul),
                              ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    e += [crit, Spacer(1, 8)]

    # Indicadores del resumen
    kpis = Table([[Paragraph(str(v), estilo_kpi_v) for v in rep["resumen"].values()],
                  [Paragraph(k, estilo_kpi_t) for k in rep["resumen"]]],
                 colWidths=[util / len(rep["resumen"])] * len(rep["resumen"]))
    kpis.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                              ("LINEBEFORE", (1, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                              ("TOPPADDING", (0, 0), (-1, -1), 5)]))
    e += [kpis, Spacer(1, 10)]

    if analisis:
        caja = Table([[Paragraph("<b>Análisis generado con inteligencia artificial (Gemini)</b>", estilo_celda)],
                      [Paragraph(analisis.replace("\n", "<br/>"), estilo_ia)]], colWidths=[util])
        caja.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE9FE")),
                                  ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#7C3AED")),
                                  ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        e += [caja, Spacer(1, 10)]

    # Tabla de datos
    cols = [c for c in TIPOS[rep["tipo"]]["columnas"]]
    total_ancho = sum(c.ancho for c in cols)
    anchos = [util * c.ancho / total_ancho for c in cols]
    datos = [[Paragraph(c.titulo, estilo_cab) for c in cols]]
    for f in rep["filas"]:
        datos.append([Paragraph(texto_celda(c, f[c.clave]).replace("&", "&amp;").replace("<", "&lt;"), estilo_celda)
                      for c in cols])
    if len(datos) == 1:
        datos.append([Paragraph("No hay registros para los criterios seleccionados.", estilo_celda)] + [""] * (len(cols) - 1))
    t = Table(datos, colWidths=anchos, repeatRows=1)
    estilo = [("BACKGROUND", (0, 0), (-1, 0), azul), ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
              ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    for i in range(1, len(datos)):
        if i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F5F8FF")))
    if not rep["filas"]:
        estilo.append(("SPAN", (0, 1), (-1, 1)))
    t.setStyle(TableStyle(estilo))
    e.append(t)
    e += [Spacer(1, 6), Paragraph(f"Total de registros: {len(rep['filas'])}", estilo_sub)]

    doc.build(e, canvasmaker=CanvasNumerado)
    return buf.getvalue()


# --------------------------------------------------------------------------- Excel
def generar_excel(rep: dict, generado_por: str, analisis: str | None = None) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    cols = TIPOS[rep["tipo"]]["columnas"]
    n = len(cols)
    ultima = get_column_letter(n)
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte"
    azul = PatternFill("solid", fgColor=AZUL[1:])
    claro = PatternFill("solid", fgColor=AZUL_CLARO[1:])
    cebra = PatternFill("solid", fgColor="F5F8FF")
    borde = Border(*(Side(style="thin", color="CBD5E1"),) * 4)
    fuente = "Calibri"

    ws.merge_cells(f"A1:{ultima}1")
    ws["A1"] = f"{NOMBRE_APP} — {rep['titulo']}"
    ws["A1"].font = Font(name=fuente, size=16, bold=True, color="FFFFFF")
    ws["A1"].fill = azul
    ws["A1"].alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[1].height = 30
    ws.merge_cells(f"A2:{ultima}2")
    ws["A2"] = f"{INSTITUCION} · Generado el {fmt_fecha(ahora_local())} por {generado_por}"
    ws["A2"].font = Font(name=fuente, size=10, italic=True, color=GRIS[1:])
    ws.merge_cells(f"A3:{ultima}3")
    ws["A3"] = "Criterios: " + texto_criterios(rep)
    ws["A3"].font = Font(name=fuente, size=10, bold=True, color=AZUL[1:])
    ws["A3"].fill = claro
    ws.merge_cells(f"A4:{ultima}4")
    ws["A4"] = "Resumen: " + " · ".join(f"{k}: {v}" for k, v in rep["resumen"].items())
    ws["A4"].font = Font(name=fuente, size=10)

    fila_cab = 6
    for i, c in enumerate(cols, start=1):
        celda = ws.cell(row=fila_cab, column=i, value=c.titulo)
        celda.font = Font(name=fuente, bold=True, color="FFFFFF")
        celda.fill = azul
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celda.border = borde
        ws.column_dimensions[get_column_letter(i)].width = max(12, c.ancho * 16)
    ws.row_dimensions[fila_cab].height = 22

    for j, f in enumerate(rep["filas"], start=fila_cab + 1):
        for i, c in enumerate(cols, start=1):
            v = f[c.clave]
            if c.tipo == "porcentaje":
                valor = None if v is None else float(v) / 100
            elif c.tipo == "numero":
                valor = int(v)
            else:
                valor = v
            celda = ws.cell(row=j, column=i, value=valor if valor is not None else ("No aplica" if c.tipo == "porcentaje" else ""))
            celda.font = Font(name=fuente, size=10)
            celda.border = borde
            celda.alignment = Alignment(vertical="top", wrap_text=True)
            if c.tipo == "fechahora":
                celda.number_format = "dd/mm/yyyy hh:mm AM/PM"
            elif c.tipo == "porcentaje" and valor is not None:
                celda.number_format = "0.0%"
            if (j - fila_cab) % 2 == 0:
                celda.fill = cebra
    fin = fila_cab + max(len(rep["filas"]), 1)
    if not rep["filas"]:
        ws.cell(row=fila_cab + 1, column=1, value="No hay registros para los criterios seleccionados.")
    ws.cell(row=fin + 2, column=1, value=f"Total de registros: {len(rep['filas'])}").font = Font(name=fuente, bold=True)
    ws.freeze_panes = ws.cell(row=fila_cab + 1, column=1)
    ws.auto_filter.ref = f"A{fila_cab}:{ultima}{fin}"

    # Formato de impresión: horizontal, ajustado al ancho, encabezado y pie
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f"{fila_cab}:{fila_cab}"
    ws.oddHeader.center.text = f"{NOMBRE_APP} · {rep['titulo']}"
    ws.oddFooter.left.text = "Generado el &D"
    ws.oddFooter.right.text = "Página &P de &N"

    if analisis:
        ia = wb.create_sheet("Análisis IA")
        ia["A1"] = "Análisis generado con inteligencia artificial (Gemini)"
        ia["A1"].font = Font(name=fuente, size=14, bold=True, color="5B21B6")
        for k, linea in enumerate([x for x in analisis.split("\n") if x.strip()], start=3):
            ia.cell(row=k, column=1, value=linea.strip()).alignment = Alignment(wrap_text=True, vertical="top")
        ia.column_dimensions["A"].width = 120

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
