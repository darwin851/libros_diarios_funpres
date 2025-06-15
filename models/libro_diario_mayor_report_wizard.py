from odoo import models, fields, api
import logging
import io
import xlsxwriter
import base64

from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LibroDiarioMayorReportWizard(models.TransientModel):
    _name = 'libro.diario.mayor.report.wizard'
    _description = 'Wizard para generar reporte Libro Diario Mayor'

    date_from = fields.Date(string='Fecha de Inicio', required=True)
    date_to = fields.Date(string='Fecha de Fin', required=True)

    archivo_excel = fields.Binary(string="Archivo Excel", readonly=True)
    archivo_nombre = fields.Char(string="Libro Diario")

    export_format = fields.Selection([
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
    ], string='Formato de Exportación', default='pdf')

    def action_generate_mayor_report(self):
        # Nota: Asegúrate de que el external ID usado aquí coincida con el definido en el XML del reporte.
        # Por ejemplo, si en el XML lo defines como:
        #    id="report_pdf_libro_diario_mayor"
        # y tu módulo se llama "libro_diario_report", la referencia completa sería:
        #    'libro_diario_report.report_pdf_libro_diario_mayor'
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

        self.archivo_nombre = f"Libro Diario Mayor (PDF) - {mes}"

        data = {
            'date_from': self.date_from.strftime('%Y-%m-%d'),
            'date_to': self.date_to.strftime('%Y-%m-%d'),
        }

        if self.export_format == 'xlsx':
            print("DAG: seleccione Excel Libro diario mayor report")
            return self.generar_reporte_excel(data)
        elif self.export_format == 'pdf':
            return self.env.ref('libro_diario_report.action_libro_diario_mayor_pdf').report_action(self, data)

    def generar_reporte_excel(self, data):
        """
            Genera un .xlsx con el Libro Diario Mayor y
            devuelve la acción de descarga en el navegador.
            Incluye al inicio:
              - Empresa
              - Usuario
              - Periodo (date_from – date_to)
            """
        date_from = self.date_from
        date_to = self.date_to

        # 1) Recopilar datos de cuentas (tu rutina intacta)
        _logger.info("Iniciando cálculo de cuentas para Excel")
        Group = self.env['account.group']
        Account = self.env['account.account']
        MoveLine = self.env['account.move.line']

        groups = Group.search([('code_prefix_start', '!=', False)])
        groups = groups.filtered(lambda g: len(g.code_prefix_start.strip()) == 4)
        accounts_data = []
        for group in groups:
            accounts = Account.search([('group_id', 'child_of', group.id)])
            if not accounts:
                continue
            ids = accounts.ids

            init = MoveLine.read_group([
                ('account_id', 'in', ids),
                ('date', '<', date_from),
                ('move_id.state', '=', 'posted'),
            ], ['balance'], [])
            initial = init and init[0].get('balance') or 0.0

            period = MoveLine.read_group([
                ('account_id', 'in', ids),
                ('date', '>=', date_from),
                ('date', '<=', date_to),
                ('move_id.state', '=', 'posted'),
            ], ['debit', 'credit'], [])
            debit = period and period[0].get('debit') or 0.0
            credit = period and period[0].get('credit') or 0.0

            final = initial + debit - credit
            if not any([initial, debit, credit]):
                continue

            accounts_data.append({
                'code': group.code_prefix_start,
                'name': group.name,
                'saldo_inicial': initial,
                'debe': debit,
                'haber': credit,
                'saldo_final': final,
            })
        _logger.info(f"Datos listos: {len(accounts_data)} líneas")

        # 2) Crear workbook en memoria
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = workbook.add_worksheet('Libro Diario Mayor')

        # 3) Formatos
        bold = workbook.add_format({'bold': True})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3'})
        money = workbook.add_format({'num_format': '#,##0.00'})
        info_fmt = workbook.add_format({'italic': True})
        title_fmt = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
        })

        top_money = workbook.add_format({
            'num_format': '#,##0.00',
            'top': 1,  # Borde superior de una línea
            'top_color': 'black'  # Opcional: color del borde
        })

        # 4) Escribir datos de cabecera (empresa, usuario y periodo)
        company_name = self.env.company.name
        user_name = self.env.user.name
        ws.merge_range(0, 0, 0, 5, company_name, title_fmt)
        ws.merge_range(1, 0, 1, 5, 'LIBRO DIARIO MAYOR', title_fmt)
        ws.write(2, 0, 'Impreso por:', bold)
        ws.write(2, 1, user_name, info_fmt)
        ws.write(3, 0, 'Periodo:', bold)
        ws.write(3, 1, f"{date_from}  a  {date_to}", info_fmt)

        # 5) Encabezados de la tabla (comienzan en la fila 4, índice 4)
        headers = [
            'Código de Cuenta',
            'Nombre de la Cuenta',
            'Saldo Inicial',
            'Debe',
            'Haber',
            'Saldo Final',
        ]
        header_row = 5
        for col, title in enumerate(headers):
            ws.write(header_row, col, title, header_fmt)

        # 6) Rellenar filas de datos justo debajo de los encabezados
        for idx, acct in enumerate(accounts_data, start=header_row + 1):
            ws.write(idx, 0, acct['code'])
            ws.write(idx, 1, acct['name'])
            ws.write_number(idx, 2, acct['saldo_inicial'], money)
            ws.write_number(idx, 3, acct['debe'], money)
            ws.write_number(idx, 4, acct['haber'], money)
            ws.write_number(idx, 5, acct['saldo_final'], money)

        # 7) Totales en pie de tabla
        total_row = header_row + 1 + len(accounts_data)
        ws.write(total_row, 1, 'Totales', bold)
        # Columnas C, D, E, F corresponden a índices 2,3,4,5
        for idx, col_letter in enumerate(['C', 'D', 'E', 'F'], start=2):
            fmt = top_money if col_letter in ('D', 'E') else money
            ws.write_formula(
                total_row, idx,
                f"=SUM({col_letter}{header_row + 2}:{col_letter}{total_row})",
                fmt
            )

        workbook.close()
        output.seek(0)
        data_xlsx = output.read()

        # 8) Guardar en campos binarios para descarga
        archivo = base64.b64encode(data_xlsx)
        nombre = f"Libro_Diario_Mayor_{date_from}_{date_to}.xlsx"
        self.write({
            'archivo_excel': archivo,
            'archivo_nombre': nombre,
        })

        # 9) Acción de descarga
        return {
            'type': 'ir.actions.act_url',
            'url': (
                '/web/content/?model=libro.diario.mayor.report.wizard'
                f'&field=archivo_excel&filename={nombre}&id={self.id}&download=true'
            ),
            'target': 'self',
        }

    def _get_leaf_categories(self, group):
        # Buscar subgrupos cuyo parent_id sea el id del grupo actual
        children = self.env['account.group'].search([('parent_id', '=', group.id)])
        if not children:
            return group
        leaf_set = self.env['account.group']
        for child in children:
            leaf_set |= self._get_leaf_categories(child)
        return leaf_set

    def _get_accounts_data(self, date_from, date_to):
        _logger.info("Iniciando el cálculo de cuentas de mayor con 4 dígitos en code_prefix_start")
        Group = self.env['account.group']
        Account = self.env['account.account']
        MoveLine = self.env['account.move.line']

        # Buscar todos los grupos con code_prefix_start definido y filtrar los que tengan 4 dígitos.
        groups = Group.search([('code_prefix_start', '!=', False)])
        groups = groups.filtered(lambda g: len(g.code_prefix_start.strip()) == 4)
        _logger.info(f"Se encontraron {len(groups)} grupos con 4 dígitos en code_prefix_start")

        accounts_data = []
        # Recorrer cada grupo mayor encontrado
        for group in groups:
            _logger.info(f"Procesando grupo: {group.name} (Código: {group.code_prefix_start})")

            # Buscar todas las cuentas asociadas al grupo y sus subgrupos
            accounts = Account.search([('group_id', 'child_of', group.id)])
            if not accounts:
                _logger.info(f"No se encontraron cuentas asociadas al grupo {group.code_prefix_start}")
                continue

            account_ids = accounts.ids
            _logger.info(f"Se encontraron {len(account_ids)} cuentas asociadas al grupo {group.code_prefix_start}")

            # Calcula el saldo inicial: movimientos anteriores a date_from
            domain_initial = [
                ('account_id', 'in', account_ids),
                ('date', '<', date_from),
                ('move_id.state', '=', 'posted'),
            ]
            initial_data = MoveLine.read_group(domain_initial, ['balance'], [])
            _logger.info(f"Resultados para saldo inicial del grupo {group.code_prefix_start}: {initial_data}")
            initial_balance = (
                initial_data[0]['balance'] if initial_data and initial_data[0].get('balance') is not None else 0.0
            )

            # Calcula los movimientos en el período [date_from, date_to]
            domain_period = [
                ('account_id', 'in', account_ids),
                ('date', '>=', date_from),
                ('date', '<=', date_to),
                ('move_id.state', '=', 'posted'),
            ]
            period_data = MoveLine.read_group(domain_period, ['debit', 'credit'], [])
            _logger.info(f"Resultados del período para el grupo {group.code_prefix_start}: {period_data}")
            total_debit = (
                period_data[0]['debit'] if period_data and period_data[0].get('debit') is not None else 0.0
            )
            total_credit = (
                period_data[0]['credit'] if period_data and period_data[0].get('credit') is not None else 0.0
            )

            final_balance = initial_balance + total_debit - total_credit
            _logger.info(
                f"Grupo {group.code_prefix_start}: Saldo Inicial: {initial_balance}, Debe: {total_debit}, "
                f"Haber: {total_credit}, Saldo Final: {final_balance}"
            )

            # Si los valores son todos cero, se omite este grupo.
            if initial_balance == 0.0 and total_debit == 0.0 and total_credit == 0.0:
                _logger.info(f"Grupo {group.code_prefix_start} omitido por tener valores cero")
                continue

            accounts_data.append({
                'code': group.code_prefix_start,
                'name': group.name,
                'saldo_inicial': initial_balance,
                'debe': total_debit,
                'haber': total_credit,
                'saldo_final': final_balance,
            })

        _logger.info(f"Cálculo completado con {len(accounts_data)} registros de grupos de mayor (con valores > 0)")
        return accounts_data
