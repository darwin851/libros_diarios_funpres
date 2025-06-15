from odoo import models, fields


class LibroAuxiliarReportWizard(models.TransientModel):
    _name = 'libro.auxiliar.wizard'
    _description = 'Asistente Libro Auxiliar'

    date_from = fields.Date(string="Desde", required=True)
    date_to = fields.Date(string="Hasta", required=True)
    all_subs = fields.Boolean(string="Incluir subcuentas", default=True)
    account_start = fields.Many2one('account.account', string="Cuenta inicio", required=True)
    account_end = fields.Many2one('account.account', string="Cuenta fin", required=True)

    def action_generate_auxiliar(self):
        return self.env.ref('libro_diario_report.action_libro_auxiliar_pdf') \
            .report_action(self)
