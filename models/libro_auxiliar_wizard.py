# File: models/libro_auxiliar_wizard.py
from odoo import api, fields, models
from odoo.exceptions import UserError


class LibroAuxiliarWizard(models.TransientModel):
    _name = 'libro.auxiliar.wizard'
    _description = 'Wizard Auxiliar de Mayor'

    date_from = fields.Date(string='Desde', required=True)
    date_to = fields.Date(string='Hasta', required=True)
    all_subs = fields.Boolean(string='Todas las subcuentas', default=True)
    account_start = fields.Many2one(
        'account.account', string='Desde Cuenta', required=True,
        help='Seleccione la cuenta desde (grupo o detalle)'
    )
    account_end = fields.Many2one(
        'account.account', string='Hasta Cuenta', required=True,
        help='Seleccione la cuenta hasta (detalle)'
    )

    @api.onchange('account_start')
    def _onchange_account_start(self):
        if not self.account_start:
            return {'domain': {'account_end': []}}
        return {'domain': {
            'account_end': [
                ('group_id', 'child_of', self.account_start.group_id.id),
                ('code', '>=', self.account_start.code),
            ]
        }}

    def action_print_pdf(self):
        if self.date_from > self.date_to:
            raise UserError('La fecha Desde debe ser anterior o igual a Hasta.')
        return self.env.ref('libro_diario_report.action_libro_auxiliar_pdf').report_action(self)

    def action_export_excel(self):
        # Llama a tu método de generación de Excel
        return self.generar_reporte_excel()

    generar_reporte_excel = fields.Binary(string='Generar Excel')

    @api.model
    def get_preview_data(self, wizard_ids, options):
        # Devuelve la lista de filas para la previsualización OWL según la maqueta
        wiz = self.browse(wizard_ids[0])
        date_from = options.get('date_from')
        date_to = options.get('date_to')
        all_subs = options.get('all_subs')
        start_id = options.get('account_start')
        end_id = options.get('account_end')
        # Obtener cuentas detalle en rango de código
        start_acc = self.env['account.account'].browse(start_id)
        end_acc = self.env['account.account'].browse(end_id)
        domain_acc = [
            ('code', '>=', start_acc.code),
            ('code', '<=', end_acc.code),
        ]
        # Si no todas las subcuentas, filtrar por grupo de inicio
        if not all_subs:
            domain_acc.append(('group_id', 'child_of', start_acc.group_id.id))
        accounts = self.env['account.account'].search(domain_acc, order='group_id,code')
        rows = []
        # Agrupar por grupo_id
        groups = {}
        for acc in accounts:
            grp = acc.group_id
            if grp.id not in groups:
                groups[grp.id] = grp
        for grp in groups.values():
            rows.append({
                'type': 'group',
                'id': f"group_{grp.id}",
                'code': grp.code_prefix_start or '',
                'name': grp.name,
            })
            # Detalles de cuenta
            grp_accounts = [a for a in accounts if a.group_id.id == grp.id]
            for acc in grp_accounts:
                # Saldo inicial
                init_data = self.env['account.move.line'].read_group([
                    ('account_id', '=', acc.id),
                    ('date', '<', date_from),
                    ('move_id.state', '=', 'posted'),
                ], ['balance'], [])
                initial_balance = init_data and init_data[0].get('balance', 0.0) or 0.0
                rows.append({
                    'type': 'detail',
                    'id': f"detail_{acc.id}",
                    'code': acc.code,
                    'name': acc.name,
                    'initial_balance': initial_balance,
                })
                # Movimientos del período
                move_lines = self.env['account.move.line'].search([
                    ('account_id', '=', acc.id),
                    ('date', '>=', date_from),
                    ('date', '<=', date_to),
                    ('move_id.state', '=', 'posted'),
                ], order='date,move_id')
                total_debit = total_credit = 0.0
                for ln in move_lines:
                    rows.append({
                        'type': 'move',
                        'id': f"move_{ln.id}",
                        'move_name': ln.move_id.name,
                        'date': ln.date,
                        'label': ln.name,
                        'debit': ln.debit,
                        'credit': ln.credit,
                    })
                    total_debit += ln.debit
                    total_credit += ln.credit
                # Totales cuenta
                final_balance = initial_balance + total_debit - total_credit
                rows.append({
                    'type': 'total',
                    'id': f"total_{acc.id}",
                    'total_debit': total_debit,
                    'total_credit': total_credit,
                    'final_balance': final_balance,
                })
        return rows
