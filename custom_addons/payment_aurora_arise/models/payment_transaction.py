import logging
import pprint

from werkzeug import urls

from odoo import _, models
from odoo.exceptions import ValidationError

from odoo.addons.payment.const import CURRENCY_MINOR_UNITS
from odoo.addons.payment_aurora_arise import const
from odoo.addons.payment_aurora_arise.controllers.main import AuroraController

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_processing_values(self, processing_values):
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != 'aurora_arise':
            return res

        base_url = self.provider_id.get_base_url()
        return {
            'client_secret': 'your_client_secret',
            'return_url': urls.url_join(base_url, '/payment/aurora_arise/return'),
            'cancel_url': urls.url_join(base_url, '/payment/aurora_arise/cancel'),
        }

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Aurora-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific rendering values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'aurora_arise':
            return res

        payload = self._aurora_prepare_payment_request_payload()
        _logger.info("sending '/payments' request for link creation:\n%s", pprint.pformat(payload))
        payment_data = self.provider_id._aurora_make_request('/payments', data=payload) #TODO update endpoint

        # The provider reference is set now to allow fetching the payment status after redirection
        self.provider_reference = payment_data.get('id')

        # Extract the checkout URL from the payment data and add it with its query parameters to the
        # rendering values. Passing the query parameters separately is necessary to prevent them
        # from being stripped off when redirecting the user to the checkout URL, which can happen
        # when only one payment method is enabled on Aurora and query parameters are provided.
        checkout_url = payment_data['_links']['checkout']['href']
        parsed_url = urls.url_parse(checkout_url)
        url_params = urls.url_decode(parsed_url.query)
        return {'api_url': checkout_url, 'url_params': url_params}

    def _send_payment_request(self):
        """ Override of payment to send a payment request to Aurora ARISE.
        
        Note: self.ensure_one()

        :return: None
        :raise: ValidationError if the transaction is not linked to a token
        """
        super()._send_payment_request()
        if self.provider_code != 'aurora_arise':
            return

        # Ensure all required data is present
        if not self.token_id:
            raise UserError("Aurora: " + _("The transaction is not linked to a token."))

        try:
            # Prepare the payment data
            payment_data = self._aurora_prepare_payment_request_payload()

            # Make the payment request
            response = self.provider_id._aurora_make_request('/pay-api/v1/transactions/sale', data=payload)

            # Log the payment response (excluding sensitive data)
            _logger.info(
                "Payment request response for transaction with reference %s:\n%s",
                self.reference,
                self._get_safe_logging_data(response)
            )

            # Handle the payment response
            self._handle_aurora_payment_response(response)

        except ValidationError as e:
            _logger.exception(
                "Validation error processing payment for transaction with reference %s",
                self.reference
            )
            self._set_error(str(e))
        except Exception as e:
            _logger.exception(
                "Error processing payment for transaction with reference %s",
                self.reference
            )
            self._set_error("Aurora: " + _("Could not process the payment: %s", str(e)))

    def _aurora_prepare_payment_request_payload(self):
        """ Create the payload for the payment request based on the transaction values.

        :return: The request payload
        :rtype: dict
        """
        user_lang = self.env.context.get('lang')
        base_url = self.provider_id.get_base_url()
        redirect_url = urls.url_join(base_url, AuroraController._return_url)
        webhook_url = urls.url_join(base_url, AuroraController._webhook_url)
        decimal_places = CURRENCY_MINOR_UNITS.get(
            self.currency_id.name, self.currency_id.decimal_places
        )
        payment_data = {
                'paymentProcessorId': '4551afdb-5db9-4514-8526-bf9084f17569',
                'accountNumber': post.get('card_number').replace(' ', ''),
                'expirationMonth': int(post.get('expiry_date').split('/')[0]),
                'expirationYear': int('20' + post.get('expiry_date').split('/')[1]),
                'securityCode': post.get('cvv'),
                'amount': transaction.amount,
                'currencyId': 1,
                'referenceId': transaction.reference,
            }
    
    def _handle_aurora_payment_response(self, response):
        """ Handle the payment response from Aurora ARISE.

        :param dict response: The API response
        :return: None
        :raise: ValidationError if the payment fails
        """
        # Check payment status
        status = response.get('status')
        if status in ['Authorized', 'Captured']:
            self._set_done()
            # Store the transaction ID from Aurora
            self.provider_reference = response.get('id')
        elif status == 'Pending':
            self._set_pending()
        elif status in ['Declined', 'Canceled', 'Failed']:
            error_msg = response.get('error', {}).get('message', 'Unknown error')
            self._set_error(_("Payment failed: %s", error_msg))
        else:
            self._set_error(_("Received unknown payment status: %s", status))
        
    def _get_safe_logging_data(self, response):
        """ Remove sensitive data before logging.

        :param dict response: The API response
        :return: The sanitized response data
        :rtype: dict
        """
        if not response:
            return {}

        # Create a copy of the response
        safe_response = response.copy()

        # Remove sensitive fields
        sensitive_fields = ['card_number', 'cvv', 'access_token']
        for field in sensitive_fields:
            safe_response.pop(field, None)

        return safe_response


    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on Aurora data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'aurora_arise' or len(tx) == 1:
            return tx

        tx = self.search(
            [('reference', '=', notification_data.get('ref')), ('provider_code', '=', 'aurora_arise')]
        )
        if not tx:
            raise ValidationError("Aurora: " + _(
                "No transaction found matching reference %s.", notification_data.get('ref')
            ))
        return tx

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on Aurora data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'aurora_arise':
            return

        payment_data = self.provider_id._aurora_make_request(
            f'/pay-api/v1/transactions/{self.provider_reference}', method="GET"
        )

        # Update the payment method.
        payment_method_type = payment_data.get('paymentMethodType', '')
        if payment_method_type == 'Card':
            payment_method_type = payment_data.get('details', {}).get('cardLabel', '').lower()
        payment_method = self.env['payment.method']._get_from_code(
            payment_method_type, mapping=const.PAYMENT_METHODS_MAPPING
        )
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        payment_status = payment_data.get('status')
        if payment_status == 'Pending':
            self._set_pending()
        elif payment_status == 'Authorized':
            self._set_authorized()
        elif payment_status == 'paid': #TODO is this captured, settled or what?
            self._set_done()
        elif payment_status in ['Declined', 'Canceled', 'Failed']:
            self._set_canceled("Aurora: " + _("Cancelled payment with status: %s", payment_status))
        else:
            _logger.info(
                "received data with invalid payment status (%s) for transaction with reference %s",
                payment_status, self.reference
            )
            self._set_error(
                "Aurora: " + _("Received data with invalid payment status: %s", payment_status)
            )
