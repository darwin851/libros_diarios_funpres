from odoo import models, fields, api
from odoo.exceptions import ValidationError
import io
import xlsxwriter
import base64

class LibroDiarioReportWizard(models.TransientModel):
    _name = 'libro.diario.report.wizard'
    _description = 'Asistente para Generar Libro Diario'

    date_from = fields.Date(string='Desde')
    date_to = fields.Date(string='Hasta')

    archivo_excel = fields.Binary(string="Archivo Excel", readonly=True)
    archivo_nombre = fields.Char(string="Libro Diario")



    # Añade la definición del campo aquí:
    export_format = fields.Selection([
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
        # Agrega otros formatos si los necesitas
    ], string="Formato de Exportación", required=True, default='pdf')

    def action_generate_report(self):
        MESES_ES = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre"
        }

        if not self.date_from or not self.date_to:
            raise ValidationError("Selecionar las fechas Desde y Hasta.")

        if self.date_to < self.date_from:
            raise ValidationError("La fecha Hasta no puede ser menor que la fecha Desde.")

        mes = MESES_ES.get(self.date_from.month, 'Mes')

        print(mes)

        self.archivo_nombre = f"Libro Diario (PDF) - {mes}"

        if self.export_format == 'xlsx':
            print("DAG: seleccione Excel")
            return self.generar_reporte_excel()
        elif self.export_format == 'pdf':
            return self.env.ref('libro_diario_report.action_libro_diario_pdf').report_action(self, data={
                'date_from': self.date_from.strftime('%Y-%m-%d'),
                'date_to': self.date_to.strftime('%Y-%m-%d'),
            })

    def generar_reporte_excel(self):
        moves = self.env['account.move'].search([
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '=', 'posted')
        ], order='date, id')

        if not moves:
            raise ValidationError("No se encontraron asientos contables en el rango de fechas seleccionado.")

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Libro Diario")

        bold = workbook.add_format({'bold': True})
        money = workbook.add_format({'num_format': '#,##0.00'})
        normal = workbook.add_format({'text_wrap': True, 'valign': 'TOP'})

        # Estilo de borde: 1 = fino, 2 = medio, 5 = grueso, etc.
        border_style = 1

        # Para la fila "Total del Asiento"
        total_asiento_label_format = workbook.add_format({
            'bold': True,
            'top': border_style
        })
        total_asiento_amount_format = workbook.add_format({
            'bold': True,  # Totales de asiento también en negrita
            'num_format': '#,##0.00',
            'top': border_style
        })

        # Para la fila "TOTAL GENERAL"
        total_general_label_format = workbook.add_format({
            'bold': True,
            'top': border_style
        })
        total_general_amount_format = workbook.add_format({
            'bold': True,
            'num_format': '#,##0.00',  # Totales generales sin negrita (según código original)
            'top': border_style
        })

        headers = ['Fecha', 'Diario', 'N. Asiento', 'Cuenta', 'Nombre de la cuenta',  'Debe', 'Haber']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, bold)

        # (Ajusta estos valores según tus preferencias)
        worksheet.set_column(0, 0, 12)  # Columna A: Fecha
        worksheet.set_column(1, 1, 25)  # Columna B: Diario
        worksheet.set_column(2, 2, 18)  # Columna C: N. Asiento
        worksheet.set_column(3, 3, 20)  # Columna D: Cuenta
        worksheet.set_column(4, 4, 60)  # Columna E: Nombre de la cuenta
        worksheet.set_column(5, 5, 15)  # Columna G: Debe
        worksheet.set_column(6, 6, 15)  # Columna H: Haber

        row = 1
        total_debe_general = 0.00
        total_haber_general = 0.00

        for move in moves:
            total_debe_asiento = 0.00
            total_haber_asiento = 0.00
            for line in move.line_ids:
                if line.display_type in ('line_section', 'line_note'):
                    continue  # omitir líneas no contables

                worksheet.write(row, 0, str(move.date), normal)
                worksheet.write(row, 1, move.journal_id.name, normal)
                worksheet.write(row, 2, move.name, normal)
                worksheet.write(row, 3, line.account_id.code or '', normal)
                worksheet.write(row, 4, line.account_id.name or '', normal)
                worksheet.write(row, 5, line.debit, money)
                worksheet.write(row, 6, line.credit, money)

                total_debe_asiento += line.debit
                total_haber_asiento += line.credit
                row += 1

            #totales de asiento
            worksheet.write(row, 4, "Total del Asiento", total_asiento_label_format)
            worksheet.write(row, 5, total_debe_asiento, total_asiento_amount_format)
            worksheet.write(row, 6, total_haber_asiento, total_asiento_amount_format)
            row += 2

            total_debe_general += total_debe_asiento
            total_haber_general += total_haber_asiento

        # Total general
        worksheet.write(row, 4, "TOTAL GENERAL", total_general_label_format)
        worksheet.write(row, 5, total_debe_general, total_general_amount_format)
        worksheet.write(row, 6, total_haber_general, total_general_amount_format)

        workbook.close()
        output.seek(0)
        archivo = base64.b64encode(output.read())

        self.write({
            'archivo_excel': archivo,
            'archivo_nombre': f'Libro_Diario_{self.date_from}_{self.date_to}.xlsx'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=libro.diario.report.wizard&field=archivo_excel&filename=%s&id=%s&download=true' % (
                self.archivo_nombre, self.id),
            'target': 'self',
        }




