import logging
import pprint

import requests
from werkzeug import urls

from odoo import _, fields, models, service
from odoo.exceptions import ValidationError

from odoo.addons.payment_aurora_arise import const

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('aurora_arise', 'Aurora ARISE')], ondelete={'aurora_arise': 'set default'}
    )
    aurora_client_id = fields.Char(
        string="Aurora Client ID",
        help="The Test or Live API ID depending on the configuration of the provider",
        groups="base.group_system"
    )
    aurora_client_secret = fields.Char(
        string="Aurora Client Secret",
        help="The Test or Live API Secret depending on the configuration of the provider",
        groups="base.group_system"
    )
    aurora_payment_processor_id = fields.Char(
        string="Payment Processor ID",
        help="The Payment Processor ID from the payment configurations",
        groups="base.group_system"
    )
    aurora_api_url = fields.Char(
        string="API URL",
        help="The URL to use for the API calls",
        groups="base.group_system"
    )

    #=== BUSINESS METHODS ===#

    def _get_supported_currencies(self):
        """ Override of `payment` to return the supported currencies. """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'aurora_arise':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    def _aurora_make_request(self, endpoint, data=None, method='POST'):
        """ Make a request at aurora endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request
        :param dict data: The payload of the request
        :param str method: The HTTP method of the request
        :return The JSON-formatted content of the response
        :rtype: dict
        :raise: ValidationError if an HTTP error occurs
        """
        self.ensure_one()
        url = self.aurora_api_url + endpoint

        headers = {
            "Authorization": f'Bearer {self.aurora_get_access_token()}',
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(method, url, json=data, headers=headers, timeout=60)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                _logger.exception(
                    "Invalid API request at %s with data:\n%s", url, pprint.pformat(data)
                )
                raise ValidationError(
                    "Aurora: " + _(
                        "The communication with the API failed. Aurora gave us the following "
                        "information: %s", response.json().get('detail', '')
                    ))
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach endpoint at %s", url)
            raise ValidationError(
                "Aurora: " + _("Could not establish the connection to the API.")
            )
        return response.json()
    
    def _aurora_get_access_token(self):
        self.ensure_one()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": self.aurora_client_id,
            "client_secret": self.aurora_client_secret,
            "scope": "offline_access",
        }
        url = "https://oauth.uat.arise.risewithaurora.com/oauth2/token"
        try:
            response = requests.request("POST", url, json=data, headers=headers, timeout=60)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                _logger.exception(
                    "Invalid API request at %s with data:\n%s", url, pprint.pformat(data)
                )
                raise ValidationError(
                    "Aurora: " + _(
                        "The communication with the API failed. Aurora gave us the following "
                        "information: %s", response.json().get('detail', '')
                    ))
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach endpoint at %s", url)
            raise ValidationError(
                "Aurora: " + _("Could not establish the connection to the API.")
            )
        if not access_token:
            raise ValidationError("Aurora: " + _("Could not generate a new access token."))
        access_token = response['access_token']
        return access_token

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'aurora_arise':
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES
    
    def _get_payment_processor_id(self):
        return self.aurora_payment_processor_id