"""
Unit tests for util.py
"""
import unittest
from github_approval_checker.utils import util
from github_approval_checker.utils.exceptions import ConfigError, SignatureError


class UtilUnitTests(unittest.TestCase):
    """
    Test util.py
    """

    def test_validate_config(self):
        """
        Test util.validate_config with valid configuration.
        """
        config = {
            "orgs": [
                "fake-org-1",
                "fake-org-2"
            ],
            "teams": [
                "fake-team-1",
                "fake-team-2"
            ],
            "users": [
                "fake-user"
            ],
            "admins": True
        }
        util.validate_config(config)

    def test_validate_config_bad(self):
        """
        Test util.validate_config with bad configuration data.
        """
        config = {
            "admins": "fakey"
        }

        self.assertRaises(ConfigError, util.validate_config, config)

    def test_parse_signature_bad_format(self):
        """
        Test util.parse_signature with an invalid format.
        """
        self.assertRaisesRegexp(  # pylint: disable=deprecated-method
            SignatureError,
            'Malformed signature header. Expected format: algorithm=signature',
            util.parse_signature,
            'sha1=hello=world'
        )

    def test_parse_signature_bad_algo(self):
        """
        Test util.parse_signature with an invalid algorithm
        """
        self.assertRaisesRegexp(  # pylint: disable=deprecated-method
            SignatureError,
            'Unsupported signature hash algorithm. Expected ' + util.SUPPORTED_HASH,
            util.parse_signature,
            'sha256=fake_signature'
        )

    def test_parse_signature_valid(self):
        """
        Test util.parse_signature with a valid signature header.
        """
        self.assertEqual(util.parse_signature('sha1=hello world'), 'hello world')

    def test_verify_signature_invalid(self):
        """
        Test util.validate_signature with an invalid signature.
        """
        self.assertRaisesRegexp(  # pylint: disable=deprecated-method
            SignatureError,
            'Computed signature does not match request signature.',
            util.verify_signature,
            'hello world',
            'bad-hash',
            '123456!'
        )

    def test_verify_signature_good(self):
        """
        Test util.verify_signature with a valid signature.
        """
        util.verify_signature(
            'hello world',
            '62b04606fe7f22971508503e8be2c5872d9d0140',
            '123456!'
        )

    def test_verify_unicode_signature(self):
        """
        Test util.verify_signature with a unicode-encoded string.
        An exception will be thrown by hmac.compare_digest() if the conversion fails.
        """
        util.verify_signature(
            'hello world',
            u'62b04606fe7f22971508503e8be2c5872d9d0140',
            '123456!'
        )
