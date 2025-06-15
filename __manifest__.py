{
    'name': 'Reporte Libro Diario Funpres',
    'version': '1.0',
    'depends': ['base', 'account', 'web'],
    'author': 'Darwin González',
    'category': 'Contabilidad',
    'description': 'Reporte de Libro Diario en PDF o Excel',
    'data': [
        'security/ir.model.access.csv',
        'views/libro_diario_report_wizard_view.xml',
        'views/libro_diario_mayor_report_wizard_view.xml',
        'views/libro_auxiliar_wizard_view.xml',
        'views/menu.xml',
        'report/reporte_pdf_libro_diario.xml',
        'report/report_pdf_libro_diario_mayor.xml',
        'report/libro_diario_report_template.xml',
        'report/libro_diario_mayor_report_template.xml',
        'report/libro_auxiliar_report.xml',
        'report/libro_auxiliar_report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'libro_diario_report/static/src/js/libro_auxiliar_wizard.js',
            'libro_diario_report/static/src/js/preview_table.js',
            'libro_diario_report/static/src/xml/preview_table.xml',
            'libro_diario_report/static/src/scss/libroAuxiliar.scss',
        ]
    },
    'installable': True,
    'application': True,
}
