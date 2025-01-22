{
    'name': 'Payment Provider: Aurora ARISE',
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': 'Integration with Aurora ARISE payment gateway',
    'description': """Aurora ARISE Payment Provider""",
    'author': 'Your Name',
    'website': 'https://www.example.com',
    'depends': ['payment'],
    'data': [
        'data/payment_provider_data.xml',
        'views/payment_provider_views.xml',
        'views/payment_aurora_templates.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_aurora_arise/static/src/js/payment_form.js',
            'payment_aurora_arise/static/src/css/payment_form.css',
        ],
    },
    'application': False,
    'installable': True,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}