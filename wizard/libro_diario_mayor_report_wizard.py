from odoo import models, fields

class LibroDiarioMayorReportWizard(models.TransientModel):
    _name = 'libro.diario.mayor.report.wizard'
    _description = 'Wizard para generar reporte Libro Diario Mayor'

    date_from = fields.Date(string='Fecha de Inicio', required=True)
    date_to = fields.Date(string='Fecha de Fin', required=True)
    export_format = fields.Selection([
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
    ], string='Formato de Exportación', default='pdf')

    def action_generate_mayor_report(self):
        # Llama a la lógica de los modelos para generar el reporte
        if self.export_format == 'pdf':
            return self._generate_pdf_report()

    def _generate_pdf_report(self):
        data = {
            'date_from': self.date_from.strftime('%Y-%m-%d'),
            'date_to': self.date_to.strftime('%Y-%m-%d'),
            'export_format': self.export_format,
        }
        return self.env.ref('libro_diario_report.action_libro_diario_mayor_pdf').report_action(self, data=data)

