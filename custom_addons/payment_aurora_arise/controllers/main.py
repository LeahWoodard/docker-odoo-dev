from odoo import http
from odoo.http import request
import logging
import json

_logger = logging.getLogger(__name__)

class AuroraController(http.Controller):
    @http.route('/payment/aurora_arise/form', type='http', auth='public', website=True)
    def aurora_arise_form(self, **kwargs):
        """ Render the payment form template """
        reference = kwargs.get('reference')
        transaction_id = kwargs.get('transaction_id')
        access_token = kwargs.get('access_token')
        
        if not reference or not transaction_id or not access_token:
            return request.redirect('/payment/status')
            
        transaction = request.env['payment.transaction'].sudo().browse(int(transaction_id))
        if not transaction.exists() or transaction.access_token != access_token:
            return request.redirect('/payment/status')
            
        values = {
            'reference': reference,
            'transaction_id': transaction_id,
            'access_token': access_token,
            'amount': transaction.amount,
            'currency': transaction.currency_id.name,
            'payment_form_action': '/payment/aurora_arise/process',
        }
        
        return request.render('payment_aurora_arise.aurora_arise_payment_form', values)

    @http.route('/payment/aurora_arise/process', type='json', auth='public')
    def aurora_arise_process(self, **post):
        """ Process the payment form submission """
        try:
            # Validate the transaction
            transaction_id = post.get('transaction_id')
            access_token = post.get('access_token')
            
            transaction = request.env['payment.transaction'].sudo().browse(int(transaction_id))
            if not transaction.exists() or transaction.access_token != access_token:
                return {'error': 'Invalid transaction'}
                
            # Prepare payment data
            payment_data = {
                'paymentProcessorId': '4551afdb-5db9-4514-8526-bf9084f17569',
                'accountNumber': post.get('o_aurora_card_number').replace(' ', ''),
                'expirationMonth': int(post.get('o_aurora_expiry_month')),
                'expirationYear': int('20' + post.get('o_aurora_expiry_year')),
                'securityCode': post.get('o_aurora_cvv'),
                'amount': transaction.amount,
                'currencyId': 1,
            }

            # Process the payment through the provider
            result = transaction.provider_id._aurora_process_payment(transaction, payment_data)
            
            if result.get('success'):
                return {
                    'success': True,
                    'redirect_url': '/payment/status'
                }
            else:
                return {
                    'error': result.get('error', 'Payment processing failed')
                }
                
        except Exception as e:
            _logger.exception("Error processing Aurora ARISE payment")
            return {'error': str(e)}