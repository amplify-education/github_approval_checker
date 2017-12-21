'''
Unit tests for github_handler.py
'''

import unittest
import json
import requests  # pylint: disable=unused-import
from mock import patch, call
from github_approval_checker.utils.github_handler import GithubHandler
from github_approval_checker.utils.exceptions import APIError


class GithubHandlerUnitTests(unittest.TestCase):
    '''
    Unit tests for github_handler.GithubHandler
    '''

    @patch('requests.get')
    def test_get_user_permission(self, requests_get):
        '''
        Test github_handler.GithubHandler.check_user_permission
        '''
        handler = GithubHandler('username', 'password')
        requests_get.return_value = GithubResponse({'permission': 'user-permission'})

        response = handler.get_user_permission('repo-name', 'fake-user')

        requests_get.assert_called_once_with(
            'https://api.github.com/repos/repo-name/collaborators/fake-user/permission',
            auth=('username', 'password')
        )
        self.assertEqual(response, 'user-permission')

    @patch('requests.post')
    def test_post_status(self, requests_post):
        '''
        Test github_handler.GithubHandler.post_status
        '''
        handler = GithubHandler('username', 'password')
        requests_post.return_value = GithubResponse(status_code=123890)

        response = handler.post_status(
            'repo-name',
            'branch-name',
            'context-string',
            'target-url',
            'reviewer-name',
            'old-description'
        )

        requests_post.assert_called_once_with(
            'https://api.github.com/repos/repo-name/statuses/branch-name',
            data=json.dumps({
                'state': 'success',
                'description': 'Overwritten based on approval from: reviewer-name Message: old-description',
                'context': 'context-string',
                'target_url': 'target-url'
            }),
            auth=('username', 'password')
        )

        self.assertEqual(response, 123890)

    @patch("requests.get")
    def test_get_statuses(self, requests_get):
        '''
        Test github_handler.GithubHandler.get_statuses
        '''
        handler = GithubHandler("username", "password")
        requests_get.return_value = GithubResponse(data={"statuses": "fake-statuses"})

        response = handler.get_statuses("repo-name", "ref-name")

        requests_get.assert_called_once_with(
            "https://api.github.com/repos/repo-name/commits/ref-name/status",
            auth=("username", "password")
        )
        self.assertEqual(response, "fake-statuses")

    @patch("requests.get")
    def test_get_organization_teams(self, requests_get):
        '''
        Test github_handler.GithubHandler.get_organization_teams
        '''
        handler = GithubHandler("username", "password")
        requests_get.side_effect = [
            GithubResponse(
                data=["1", "2", "3"],
                headers={
                    "link": '<https://fake.example.com>; rel="next"'
                }
            ),
            GithubResponse(
                data=["4", "5", "6"],
                headers={
                    "link": '<https://fake2.example.com>; rel="prev"'
                }
            )
        ]
        response = handler.get_organization_teams("org-name")
        self.assertEqual(requests_get.call_count, 2)
        requests_get.assert_has_calls([
            call(
                "https://api.github.com/orgs/org-name/teams",
                auth=('username', 'password')
            ),
            call(
                'https://fake.example.com',
                auth=('username', 'password')
            )
        ])
        self.assertEqual(response, ['1', '2', '3', '4', '5', '6'])

    @patch("github_approval_checker.utils.github_handler.GithubHandler.get_organization_teams")
    def test_get_team_id_good(self, get_org_teams):
        '''
        Test github_handler.GithubHandler.get_team_id with an existing team
        '''
        handler = GithubHandler("username", "password")
        get_org_teams.return_value = [
            {
                'slug': 'team-slug',
                'id': 123456
            }
        ]

        response = handler.get_team_id("org-name", "team-slug")

        get_org_teams.assert_called_once_with("org-name")
        self.assertEqual(response, 123456)

    @patch("github_approval_checker.utils.github_handler.GithubHandler.get_organization_teams")
    def test_get_team_id_bad(self, get_org_teams):
        '''
        Test github_handler.GithubHandler.get_team_id with an existing team
        '''
        handler = GithubHandler("username", "password")
        get_org_teams.return_value = [
            {
                'slug': 'not-team-slug',
                'id': 123456
            }
        ]
        self.assertRaises(APIError, handler.get_team_id, "org-name", "team-slug")
        get_org_teams.assert_called_once_with("org-name")

    @patch("requests.get")
    def test_get_team_members(self, requests_get):
        """
        Test github_handler.GithubHandler.get_team_members
        """
        handler = GithubHandler("username", "password")
        requests_get.return_value = GithubResponse(data="members-list")

        response = handler.get_team_members("team-id")

        requests_get.assert_called_once_with(
            "https://api.github.com/teams/team-id/members",
            auth=("username", "password")
        )
        self.assertEqual(response, "members-list")

    @patch("requests.get")
    def test_is_user_on_team_good(self, requests_get):
        """
        Test github_handler.GithubHandler.is_user_on_team for an active member
        """
        handler = GithubHandler("username", "password")
        requests_get.return_value = GithubResponse(data={'role': 'member', 'state': 'active'})

        response = handler.is_user_on_team("team-id", "user")

        requests_get.assert_called_once_with(
            "https://api.github.com/teams/team-id/memberships/user",
            auth=("username", "password")
        )
        self.assertTrue(response)

    @patch("requests.get")
    def test_is_user_on_team_pending(self, requests_get):
        """
        Test github_handler.GithubHandler.is_user_on_team for an active member
        """
        handler = GithubHandler("username", "password")
        requests_get.return_value = GithubResponse(data={'role': 'member', 'state': 'pending'})

        response = handler.is_user_on_team("team-id", "user")

        requests_get.assert_called_once_with(
            "https://api.github.com/teams/team-id/memberships/user",
            auth=("username", "password")
        )
        self.assertFalse(response)

    @patch("requests.get")
    def test_is_user_on_team_non_member(self, requests_get):
        """
        Test github_handler.GithubHandler.is_user_on_team for an active member
        """
        handler = GithubHandler("username", "password")
        requests_get.return_value = GithubResponse(data={'role': 'non-member', 'state': 'active'})

        response = handler.is_user_on_team("team-id", "user")

        requests_get.assert_called_once_with(
            "https://api.github.com/teams/team-id/memberships/user",
            auth=("username", "password")
        )
        self.assertFalse(response)

    @patch("requests.get")
    def test_is_user_in_org(self, requests_get):
        """
        Test github_handler.GithubHandler.is_user_in_org
        """
        handler = GithubHandler("username", "password")
        requests_get.return_value = GithubResponse(status_code=204)

        response = handler.is_user_in_org("org-name", "user-name")

        requests_get.assert_called_once_with(
            "https://api.github.com/orgs/org-name/members/user-name",
            auth=("username", "password")
        )
        self.assertTrue(response)

    @patch("requests.get")
    def test_get_file_contents(self, requests_get):
        """
        Test github_handler.GithubHandler.get_file_contents with an existing file
        """
        handler = GithubHandler("username", "password")
        requests_get.return_value = GithubResponse(data={"content": "ZmFrZS1maWxlLWNvbnRlbnRz"})

        response = handler.get_file_contents("repo-name", "file-path")

        requests_get.assert_called_once_with(
            "https://api.github.com/repos/repo-name/contents/file-path",
            auth=("username", "password")
        )
        self.assertEqual(response, "fake-file-contents")

    @patch("requests.get")
    def test_get_file_contents_bad(self, requests_get):
        """
        Test github_handler.GithubHandler.get_file_contents with a missing file
        """
        handler = GithubHandler("username", "password")
        requests_get.return_value = GithubResponse(status_code=404)

        try:
            handler.get_file_contents("repo-name", "file-path")
            assert False
        except APIError as err:
            self.assertEqual(
                err.response,
                ({
                    "status": "API Error",
                    "message": "File not found: repo-name/file-path"
                }, 500)
            )

        requests_get.assert_called_once_with(
            "https://api.github.com/repos/repo-name/contents/file-path",
            auth=("username", "password")
        )

    @patch("github_approval_checker.utils.github_handler.GithubHandler.get_file_contents")
    def test_get_config(self, get_contents):
        """
        Test github_handler.GithubHandler.get_config
        """
        handler = GithubHandler("username", "password")
        get_contents.return_value = "key: value"

        response = handler.get_config("repo-name", "config-filename")

        get_contents.assert_called_once_with("repo-name", "config-filename")
        self.assertEqual(response, {"key": "value"})

    @patch("github_approval_checker.utils.github_handler.GithubHandler.get_user_permission")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.is_user_on_team")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.get_team_id")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.is_user_in_org")
    def test_is_authorized_org(
            self,
            check_org_member,
            get_team_id,
            is_user_on_team,
            get_user_permission
    ):
        """
        Test github_handler.GithubHandler.is_authorized with an authorized organization user.
        """
        handler = GithubHandler("username", "password")
        whitelist = {
            "orgs": ["org-name"]
        }
        check_org_member.return_value = True

        response = handler.is_authorized("user-name", None, None, whitelist)

        check_org_member.assert_called_once_with("org-name", "user-name")
        get_team_id.assert_not_called()
        is_user_on_team.assert_not_called()
        get_user_permission.assert_not_called()
        self.assertTrue(response)

    @patch("github_approval_checker.utils.github_handler.GithubHandler.get_user_permission")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.is_user_on_team")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.get_team_id")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.is_user_in_org")
    def test_is_authorized_team(
            self,
            check_org_member,
            get_team_id,
            is_user_on_team,
            get_user_permission
    ):
        """
        Test github_handler.GithubHandler.is_authorized with an authorized team user.
        """
        handler = GithubHandler("username", "password")
        whitelist = {
            "teams": ["team-name"]
        }
        get_team_id.return_value = "team-id"
        is_user_on_team.return_value = True

        response = handler.is_authorized("user-name", "repo-owner", None, whitelist)

        check_org_member.assert_not_called()
        get_team_id.assert_called_once_with("repo-owner", "team-name")
        is_user_on_team.assert_called_once_with("team-id", "user-name")
        get_user_permission.assert_not_called()
        self.assertTrue(response)

    @patch("github_approval_checker.utils.github_handler.GithubHandler.get_user_permission")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.is_user_on_team")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.get_team_id")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.is_user_in_org")
    def test_is_authorized_team_error(
            self,
            check_org_member,
            get_team_id,
            is_user_on_team,
            get_user_permission
    ):
        """
        Test github_handler.GithubHandler.is_authorized with an authorized team user.
        """
        handler = GithubHandler("username", "password")
        whitelist = {
            "teams": ["team-name"]
        }
        get_team_id.return_value = "team-id"
        is_user_on_team.side_effect = APIError("api-error")

        response = handler.is_authorized("user-name", "repo-owner", None, whitelist)

        check_org_member.assert_not_called()
        get_team_id.assert_called_once_with("repo-owner", "team-name")
        is_user_on_team.assert_called_once_with("team-id", "user-name")
        get_user_permission.assert_not_called()
        self.assertFalse(response)

    @patch("github_approval_checker.utils.github_handler.GithubHandler.get_user_permission")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.is_user_on_team")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.get_team_id")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.is_user_in_org")
    def test_is_authorized_user(
            self,
            check_org_member,
            get_team_id,
            is_user_on_team,
            get_user_permission
    ):
        """
        Test github_handler.GithubHandler.is_authorized with an authorized user.
        """
        handler = GithubHandler("username", "password")
        whitelist = {
            "users": ["user-name"]
        }

        response = handler.is_authorized("user-name", None, None, whitelist)

        check_org_member.assert_not_called()
        get_team_id.assert_not_called()
        is_user_on_team.assert_not_called()
        get_user_permission.assert_not_called()
        self.assertTrue(response)

    @patch("github_approval_checker.utils.github_handler.GithubHandler.get_user_permission")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.is_user_on_team")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.get_team_id")
    @patch("github_approval_checker.utils.github_handler.GithubHandler.is_user_in_org")
    def test_is_authorized_admin(
            self,
            check_org_member,
            get_team_id,
            is_user_on_team,
            get_user_permission
    ):
        """
        Test github_handler.GithubHandler.is_authorized with an authorized admin.
        """
        handler = GithubHandler("username", "password")
        whitelist = {
            "admins": True
        }
        get_user_permission.return_value = "admin"

        response = handler.is_authorized("user-name", "repo-owner", "repo-name", whitelist)

        check_org_member.assert_not_called()
        get_team_id.assert_not_called()
        is_user_on_team.assert_not_called()
        get_user_permission.assert_called_once_with("repo-owner/repo-name", "user-name")
        self.assertTrue(response)


class GithubResponse(object):
    '''
    Mock object for Github API Responses.
    '''
    def __init__(self, data=None, status_code=999, headers=None):
        '''
        Create a mock response with the given json and statuscode.
        '''
        self.data = data
        self.status_code = status_code
        self.headers = headers

    def json(self):
        '''
        Get the fake json response
        '''
        return self.data

    def raise_for_status(self):
        '''
        Fake stand in method
        '''
        pass
