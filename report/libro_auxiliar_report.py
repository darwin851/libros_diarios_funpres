# File: report/libro_auxiliar_report.py
from odoo import api, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ReportLibroAuxiliar(models.AbstractModel):
    _name = 'report.libro_diario_report.libro_auxiliar_report_template_pdf'
    _description = 'Reporte Auxiliar de Mayor'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Obtener el wizard
        wizard = self.env['libro.auxiliar.wizard'].browse(docids)
        if not wizard:
            raise UserError("No se encontró el wizard para generar el reporte.")
        # Parámetros
        date_from = wizard.date_from
        date_to = wizard.date_to
        all_subs = wizard.all_subs
        start_acc = wizard.account_start
        end_acc = wizard.account_end

        _logger.info("📋 Libro Auxiliar: wizard id=%s, desde=%s, hasta=%s, all_subs=%s, start=%s, end=%s",
                     wizard.id, date_from, date_to, all_subs,
                     start_acc.code if start_acc else None,
                     end_acc.code if end_acc else None)

        # Validación de fechas
        if date_from > date_to:
            raise UserError("La fecha Desde debe ser anterior o igual a Hasta.")

        # Construir dominio de cuentas detalle
        domain_acc = [
            ('code', '>=', start_acc.code),
            ('code', '<=', end_acc.code),
        ]

        if not all_subs:
            domain_acc.append(('group_id', 'child_of', start_acc.group_id.id))

        accounts = self.env['account.account'].search(domain_acc, order='group_id,code')
        _logger.info("✅ Cuentas encontradas: %s", len(accounts))

        for acc in accounts:
            _logger.info("   - %s %s", acc.code, acc.name)

        rows = []
        processed_groups = set()

        for acc in accounts:
            grp = acc.group_id
            if grp.id not in processed_groups:
                # Fila de agrupadora
                rows.append({
                    'type': 'group',
                    'id': f"group_{grp.id}",
                    'code': grp.code_prefix_start or '',
                    'name': grp.name,
                })
                processed_groups.add(grp.id)

            # Fila de cuenta detalle con saldo inicial
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
            _logger.info("   > Cuenta %s: %s líneas de asientos", acc.code, len(move_lines))

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

            # Fila de totales por cuenta
            final_balance = initial_balance + total_debit - total_credit
            rows.append({
                'type': 'total',
                'id': f"total_{acc.id}",
                'total_debit': total_debit,
                'total_credit': total_credit,
                'final_balance': final_balance,
            })

        if move_lines:
            rows.append({'type': 'group', 'code': acc.code, 'name': acc.name})
            # etc.

        _logger.info("🔚 Total de filas a pintar (rows): %s", len(rows))


        # Cálculo del Total General
        total_debit_general = sum(r['total_debit'] for r in rows if r['type'] == 'total')
        total_credit_general = sum(r['total_credit'] for r in rows if r['type'] == 'total')

        return {
            'doc_ids': docids,
            'doc_model': 'libro.auxiliar.wizard',
            'docs': wizard,
            'rows': rows,
            'total_debit_general': total_debit_general,
            'total_credit_general': total_credit_general,
        }
