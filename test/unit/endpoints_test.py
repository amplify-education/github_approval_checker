"""
Unit Tests for endpoints.py
"""

import unittest
import os  # pylint: disable=unused-import
from mock import patch, call
from github_approval_checker.utils import util  # pylint: disable=unused-import
from github_approval_checker.utils.github_handler import GithubHandler  # pylint: disable=unused-import
from github_approval_checker.utils.exceptions import ConfigError, APIError, SignatureError  # noqa pylint: disable=unused-import
from github_approval_checker.api import endpoints  # pylint: disable=unused-import


class EndpointsUnitTests(unittest.TestCase):
    """
    Test endpoints.py
    """

    @patch("github_approval_checker.utils.util.verify_signature")
    @patch("github_approval_checker.api.endpoints.connexion")
    @patch("github_approval_checker.api.endpoints.GithubHandler")
    @patch("github_approval_checker.utils.util.validate_config")
    def test_post_pull_request_review(
            self,
            validate_config,
            handler_class,
            conn,
            verify_signature
    ):
        """
        Test endpoints.post_pull_request_review
        """

        conn.request.data.return_value = ''
        conn.request.headers.get.return_value = 'sha1=signature'
        verify_signature.return_value = None

        handler = handler_class.return_value
        handler.get_config.return_value = {
            "context1": [
                "whitelist1"
            ],
            "context2": [
                "whitelist2"
            ]
        }

        handler.get_statuses.return_value = [
            {
                "state": "error",
                "context": "context2",
                "target_url": "fake://status_target_2",
                "description": "Status Check 2"
            },
            {
                "state": "pending",
                "context": "context3",
                "target_url": "fake://status_target_3",
                "description": "Status Check 3"
            },
            {
                "state": "failure",
                "context": "context1",
                "target_url": "fake://status_target_1",
                "description": "Status Check 1"
            }
        ]

        handler.is_authorized.return_value = True

        validate_config.return_value = None

        data = {
            "repository": {
                "name": "repo-name",
                "full_name": "repo-full-name",
                "owner": {
                    "login": "repo-owner"
                }
            },
            "review": {
                "state": "approved",
                "commit_id": "review-commit-id",
                "user": {
                    "login": "review-user-login"
                }
            }
        }

        handler.post_status.side_effect = [
            201,
            400
        ]

        response = endpoints.post_pull_request_review(data)

        handler.get_statuses.assert_called_once_with("repo-full-name", "review-commit-id")
        self.assertEqual(handler.is_authorized.call_count, 2)
        handler.post_status.assert_has_calls([
            call(
                "repo-full-name",
                "review-commit-id",
                "context2",
                "fake://status_target_2",
                "review-user-login",
                "Status Check 2"
            ),
            call(
                "repo-full-name",
                "review-commit-id",
                "context1",
                "fake://status_target_1",
                "review-user-login",
                "Status Check 1"
            )
        ])
        self.assertEqual(response, util.STATUS_OK)

    @patch("github_approval_checker.utils.util.verify_signature")
    @patch("github_approval_checker.api.endpoints.connexion")
    @patch("github_approval_checker.api.endpoints.GithubHandler")
    @patch("github_approval_checker.utils.util.validate_config")
    def test_post_pull_request_review_unapproved(
            self,
            validate_config,
            handler_class,
            conn,
            verify_signature
    ):
        """
        Test endpoints.post_pull_request_review with a review where the status is not approved.
        """
        conn.request.data.return_value = ''
        conn.request.headers.get.return_value = 'sha1=signature'
        verify_signature.return_value = None

        handler = handler_class.return_value
        handler.get_config.return_value = {
            "context1": [
                "whitelist1"
            ],
            "context2": [
                "whitelist2"
            ]
        }

        validate_config.return_value = None

        data = {
            "repository": {
                "name": "repo-name",
                "full_name": "repo-full-name",
                "owner": {
                    "login": "repo-owner"
                }
            },
            "review": {
                "state": "changes-requested",
                "commit_id": "review-commit-id",
                "user": {
                    "login": "review-user-login"
                }
            }
        }

        response = endpoints.post_pull_request_review(data)

        handler.get_statuses.assert_not_called()
        handler.is_authorized.assert_not_called()
        handler.post_status.assert_not_called()
        self.assertEqual(response, ({'status': 'OK', 'message': 'Review state is not approved'}, 200))

    @patch("github_approval_checker.utils.util.verify_signature")
    @patch("github_approval_checker.api.endpoints.connexion")
    @patch("github_approval_checker.api.endpoints.GithubHandler")
    def test_post_pull_request_review_missing(
            self,
            handler_class,
            conn,
            verify_signature
    ):
        """
        Test endpoints.post_pull_request_review with a missing config file
        """

        conn.request.data.return_value = ''
        conn.request.headers.get.return_value = 'sha1=signature'
        verify_signature.return_value = None

        handler = handler_class.return_value
        handler.get_config.side_effect = APIError("config-error", "{'message': 'bad-config'}")

        data = {
            "repository": {
                "name": "repo-name",
                "full_name": "repo-full-name",
                "owner": {
                    "login": "repo-owner"
                }
            },
            "review": {
                "state": "changes-requested",
                "commit_id": "review-commit-id",
                "user": {
                    "login": "review-user-login"
                }
            }
        }

        response = endpoints.post_pull_request_review(data)

        handler.get_statuses.assert_not_called()
        handler.is_authorized.assert_not_called()
        handler.post_status.assert_not_called()
        self.assertEqual(response, "{'message': 'bad-config'}")

    @patch("github_approval_checker.utils.util.verify_signature")
    @patch("github_approval_checker.api.endpoints.connexion")
    @patch("github_approval_checker.api.endpoints.GithubHandler")
    @patch("github_approval_checker.utils.util.validate_config")
    def test_post_pull_request_review_bad_config(
            self,
            validate_config,
            handler_class,
            conn,
            verify_signature
    ):
        """
        Test endpoints.post_pull_request_review with a bad config file
        """

        conn.request.data.return_value = ''
        conn.request.headers.get.return_value = 'sha1=signature'
        verify_signature.return_value = None

        handler = handler_class.return_value
        handler.get_config.return_value = "config-data"

        validate_config.side_effect = ConfigError(
            'Config Validation Error',
            ({'status': 'Config Validation Error', 'message': 'Bad config data'}, 500)
        )

        data = {
            "repository": {
                "name": "repo-name",
                "full_name": "repo-full-name",
                "owner": {
                    "login": "repo-owner"
                }
            },
            "review": {
                "state": "changes-requested",
                "commit_id": "review-commit-id",
                "user": {
                    "login": "review-user-login"
                }
            }
        }

        response = endpoints.post_pull_request_review(data)

        handler.get_statuses.assert_not_called()
        handler.is_authorized.assert_not_called()
        handler.post_status.assert_not_called()
        handler.get_config.assert_called_once_with("repo-full-name", None)
        validate_config.assert_called_once_with("config-data")
        self.assertEqual(
            response,
            (
                {
                    'status': 'Config Validation Error',
                    'message': 'Bad config data'
                },
                500
            )
        )

    @patch("github_approval_checker.utils.util.verify_signature")
    @patch("github_approval_checker.api.endpoints.connexion")
    @patch("github_approval_checker.api.endpoints.GithubHandler")
    @patch("github_approval_checker.utils.util.validate_config")
    def test_post_pull_request_review_bad_sign(
            self,
            validate_config,
            handler_class,
            conn,
            verify_signature
    ):
        """
        Test endpoints.post_pull_request_review with an incorrect signature
        """

        conn.request.data.return_value = ''
        conn.request.headers.get.return_value = 'sha1=signature'
        verify_signature.side_effect = SignatureError("Error validating signature")

        response = endpoints.post_pull_request_review({})

        handler = handler_class.return_value
        handler.get_config.return_value = "config-data"

        handler.get_statuses.assert_not_called()
        handler.is_authorized.assert_not_called()
        handler.post_status.assert_not_called()
        handler.get_config.assert_not_called()
        validate_config.assert_not_called()
        self.assertEqual(
            response,
            (
                {
                    'status': 'Signature Validation Error',
                    'message': 'Error validating signature'
                },
                400
            )
        )
