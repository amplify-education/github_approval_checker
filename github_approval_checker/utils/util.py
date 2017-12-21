"""
Defines utility methods utilized by the API endpoints.
"""

import hashlib
import hmac
import jsonschema
from jsonschema import validate
from github_approval_checker.utils.exceptions import ConfigError, SignatureError

STATUS_OK = {'status': 'OK'}, 200
SUPPORTED_HASH = 'sha1'

CONFIG_SCHEMA = {
    'type': 'object',
    'properties': {
        'orgs': {
            'type': 'array',
            'items': {
                'type': 'string'
            }
        },
        'teams': {
            'type': 'array',
            'items': {
                'type': 'string'
            }
        },
        'users': {
            'type': 'array',
            'items': {
                'type': 'string'
            }
        },
        'admins': {
            'type': 'boolean'
        }
    }
}


def validate_config(config):
    """
    Validates the passed in YAML configuration against the configuration schema.
    @params config: YAML configuration to check.
    @raises ConfigError if validation of the configuration fails.
    """
    try:
        validate(config, CONFIG_SCHEMA)
    except jsonschema.exceptions.ValidationError as validated_error:
        raise ConfigError(
            'Config Validation Error: ' + str(validated_error),
            ({'status': 'Config Validation Error', 'message': str(validated_error)}, 500)
        )


def parse_signature(signature_header):
    """
    Takes the passed in signature header and checks that the associated hash
    algorithm is supported.
    @param signature_header The signature header included with the request.
    """
    try:
        algo, signature = signature_header.split("=")
    except ValueError:
        raise SignatureError('Malformed signature header. Expected format: algorithm=signature')
    if algo != SUPPORTED_HASH:
        raise SignatureError('Unsupported signature hash algorithm. Expected ' + SUPPORTED_HASH)
    return signature


def verify_signature(request_body, signature, hmac_key):
    """
    Verifies that a request body matches its accompanying signature computed with
    the configured hashing algorithm.
    @param request_body The body of the request to validate.
    @param signature    The value of the signature included with the header.
    @param hmac_key     The secret key used to compute the signature.
    """
    computed = hmac.new(hmac_key, request_body, hashlib.sha1)
    if not hmac.compare_digest(computed.hexdigest(), signature.encode('ascii', 'ignore')):
        raise SignatureError('Computed signature does not match request signature.')
