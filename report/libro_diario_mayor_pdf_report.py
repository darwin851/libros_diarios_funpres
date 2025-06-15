from odoo import models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class LibroDiarioMayorPDFReport(models.AbstractModel):
    _name = 'report.libro_diario_report.libro_diario_mayor_pdf'
    _description = 'Reporte PDF para Libro Diario Mayor'

    def _get_report_values(self, docids, data=None):
        if not data or not data.get('date_from') or not data.get('date_to'):
            raise UserError('Faltan fechas para generar el reporte.')

        date_from = data['date_from']
        date_to = data['date_to']
        wizard = self.env['libro.diario.mayor.report.wizard'].browse(docids)
        accounts_data = wizard._get_accounts_data(date_from, date_to)

        return {
            'doc_ids': docids,
            'doc_model': 'libro.diario.mayor.report.wizard',
            'data': data,
            'accounts': accounts_data,
        }