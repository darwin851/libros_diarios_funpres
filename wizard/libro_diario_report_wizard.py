from odoo import models, fields, api
from datetime import date

class LibroDiarioReportWizard(models.TransientModel):
    _name = 'libro.diario.report.wizard'
    _description = 'Asistente para generar el libro diario'

    date_from = fields.Date(string="Fecha desde", required=True, default=lambda self: date.today().replace(day=1))
    date_to = fields.Date(string="Fecha hasta", required=True, default=lambda self: date.today())
    export_format = fields.Selection([
        ('pdf', 'PDF'),
        ('excel', 'Excel')
    ], string="Formato de exportación", default='pdf', required=True)

    def action_generate_report(self):
        data = {
            'date_from': self.date_from.strftime('%Y-%m-%d'),
            'date_to': self.date_to.strftime('%Y-%m-%d'),
            'export_format': self.export_format,
        }
        if self.export_format == 'pdf':
            return self.env.ref('libro_diario_report.action_libro_diario_pdf').report_action(self, data=data)
        else:
            return self.env.ref('libro_diario_report.action_libro_diario_excel').report_action(self, data=data)
