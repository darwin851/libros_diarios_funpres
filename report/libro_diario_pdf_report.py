from odoo import models
from datetime import datetime
from odoo.exceptions import ValidationError

class ReportLibroDiarioPDF(models.AbstractModel):
    _name = 'report.libro_diario_report.libro_diario_template_pdf'
    _description = 'Reporte PDF del Libro Diario'

    def _get_report_values(self, docids, data=None):
        date_from = data.get('date_from')
        date_to = data.get('date_to')

        moves = self.env['account.move'].search([
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('state', '=', 'posted')
        ], order='date, id')

        if not moves:
            raise ValidationError("No se encontraron asientos contables en el rango de fechas seleccionado.")

        grupos = []
        total_debe_general = 0.0
        total_haber_general = 0.0

        for move in moves:
            lineas = []
            total_debe_asiento = 0.0
            total_haber_asiento = 0.0
            for line in move.line_ids:
                if line.display_type in ('line_section', 'line_note'):
                    continue
                lineas.append({
                    'fecha': move.date.strftime('%d/%m/%Y'),
                    'asiento': move.name,
                    'cuenta': line.account_id.code,
                    'nombre_cuenta': line.account_id.name,
                    'debe': line.debit,
                    'haber': line.credit
                })
                total_debe_asiento += line.debit
                total_haber_asiento += line.credit

            grupos.append({
                'asiento': move.name,
                'fecha': move.date.strftime('%d/%m/%Y'),
                'lineas': lineas,
                'total_debe_asiento': total_debe_asiento,
                'total_haber_asiento': total_haber_asiento
            })

            total_debe_general += total_debe_asiento
            total_haber_general += total_haber_asiento

        return {
            'doc_ids': docids,
            'doc_model': 'libro.diario.report.wizard',
            'data': data,
            'docs': grupos,
            'total_debe_general': total_debe_general,
            'total_haber_general': total_haber_general,
            'fecha_emision': datetime.today().strftime('%d/%m/%Y')
        }