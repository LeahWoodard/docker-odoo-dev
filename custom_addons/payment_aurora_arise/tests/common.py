from odoo.addons.payment.tests.common import PaymentCommon


class AuroraCommon(PaymentCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.aurora = cls._prepare_provider('aurora', update_values={
            'aurora_public_key': 'FLWPUBK_TEST-abcdef-X',
            'aurora_secret_key': 'FLWSECK_TEST-123456-X',
            'aurora_webhook_secret': 'coincoin_motherducker',
        })

        cls.provider = cls.aurora

        cls.redirect_notification_data = {
            'status': 'successful',
            'tx_ref': cls.reference,
        }
        cls.webhook_notification_data = {
            'event': 'charge.completed',
            'data': {
                'tx_ref': cls.reference,
            },
        }
        cls.verification_data = {
            'status': 'success',
            'data': {
                'id': '123456789',
                'status': 'successful',
                'card': {
                    'last_4digits': '2950',
                    'token': 'flw-t1nf-f9b3bf384cd30d6fca42b6df9d27bd2f-m03k',
                },
                'customer': {
                    'email': 'user@example.com',
                },
            },
        }
