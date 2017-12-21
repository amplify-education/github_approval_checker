"""
Github Handler
"""

import base64
import json
import yaml
import requests
from github_approval_checker.utils.exceptions import APIError


class GithubHandler(object):
    """
    Class to handle Github API calls
    """

    def __init__(self, github_username, github_password):
        """
        Initialize handler with with Authentication values from the environment.
        """
        self.auth = (github_username, github_password)

    def get_user_permission(self, repository_name, user_name):
        """
        Checks if a user has permissions in the repository.
        @param repository_name: The long name of the repository in the format 'owner/repo'
        @param user_name: A GitHub user's user_name
        @return user_permission: The permission of the user in that repository, being one of:
        'admin', 'write', 'read', or 'none'
        """

        request_url = 'https://api.github.com/repos/{}/collaborators/{}/permission'.format(
            repository_name, user_name)
        user_permission = requests.get(request_url, auth=self.auth)
        return user_permission.json()['permission']

    def post_status(self, repository_name, ref, context, target_url, reviewer, prior_description):
        """
        Posts a new status for the specified ref with a given context and target_url.
        @params repository_name: The full name of the repository in the format 'owner/repo'
        @params ref: It can be a SHA, a branch name, or a tag name
        @params context: String label to differentiate status from the status of other systems
        @params target_url: Target url associated with context
        @params reviewer: The username of the user that submitted the approved review
        @params prior_description: Previous status message
        """

        request_url = 'https://api.github.com/repos/{}/statuses/{}'.format(
            repository_name, ref)
        new_status = {
            'state': 'success',
            'description': 'Overwritten based on approval from: {} Message: {}'.format(
                reviewer, prior_description
            ),
            'context': context,
            'target_url': target_url
        }
        status_res = requests.post(request_url, data=json.dumps(new_status), auth=self.auth)
        return status_res.status_code

    def get_statuses(self, repository_name, ref):
        """
        Gets the combined status messages for a given ref and repository.
        @params repository_name: The full name of the repository in the format 'owner/repo'
        @params ref: The SHA, branch name, or tag name to retrieve status for.
        @return statuses: The statuses for the specified ref.
        """

        request_url = 'https://api.github.com/repos/{}/commits/{}/status'.format(
            repository_name, ref)
        combined_status = requests.get(request_url, auth=self.auth)
        return combined_status.json()['statuses']

    def get_organization_teams(self, organization_name):
        """
        Returns the list of teams in an organization.
        @params organization_name: The organization that the teams are being fetched for
        @return team_list: The list of teams in json for the organization
        """

        request_url = 'https://api.github.com/orgs/{}/teams'.format(organization_name)
        response = requests.get(request_url, auth=self.auth)
        team_list = response.json()
        running = True
        while running:
            running = False
            links = [link.split(";") for link in response.headers.get("link", "").split(",")]
            for link in links:
                if len(link) == 2 and link[1].strip() == 'rel="next"':
                    response = requests.get(link[0][1:-1], auth=self.auth)
                    running = True
                    team_list += response.json()
        return team_list

    def get_team_id(self, organization_name, team_slug):
        """
        Returns the numeric ID asssociated with a team within an organization.
        @params organization_name: The organization that the team is in.
        @params team_slug: The 'slug' name of the team.
        @raises APIError if the requested team cannot be found.
        @returns team_id: The numeric ID of the team specified.
        """
        for team in self.get_organization_teams(organization_name):
            if team['slug'] == team_slug:
                return team['id']
        raise APIError("Team not found")

    def get_team_members(self, team_id):
        """
        Returns the members of a specified team.
        @params team_id: The id for a team in an organization we are fetching members for
        @return members_list: The list of members for the team
        """

        request_url = 'https://api.github.com/teams/{}/members'.format(team_id)
        members_list = requests.get(request_url, auth=self.auth)
        return members_list.json()

    def is_user_on_team(self, team_id, user_name):
        """
        Checks that a user is an active member or maintainer within a team.
        @params team_id: The id for a team in an organization
        @params user_name: The username for the user we are checking membership for.
        @return boolean: True if the member is an active maintainer or member, False if otherwise
        """

        request_url = 'https://api.github.com/teams/{}/memberships/{}'.format(team_id, user_name)
        membership = requests.get(request_url, auth=self.auth).json()
        return membership['role'] in ['member', 'maintainer'] and membership['state'] == 'active'

    def is_user_in_org(self, organization_name, user_name):
        """
        Returns the boolean of a user's membership in an organization.
        @params organization_name: The name of an organization
        @params user_name: The username for the user we are checking membership for in an organization
        @return: boolean that denotes whether a user is a member in the organization
        """

        request_url = 'https://api.github.com/orgs/{}/members/{}'.format(organization_name, user_name)
        response = requests.get(request_url, auth=self.auth)
        return response.status_code == 204

    def get_file_contents(self, repository_name, filepath):
        """
        Get the file contents of the requested file in the specified repository.
        @params repository_name: The long name of the repository in the format 'owner/repo'.
        @params filepath: The filepath of the file to retrieve.
        @raises APIError if the file cannot be found.
        @raises requests.exceptions.HTTPError if another 4XX or 5XX error is encountered.
        @returns content: The raw contents of the specified file.
        """

        request_url = 'https://api.github.com/repos/{}/contents/{}'.format(repository_name, filepath)
        response = requests.get(request_url, auth=self.auth)
        if response.status_code == 404:
            raise APIError(
                '404 Not Found: {}/{}'.format(repository_name, filepath),
                ({
                    "status": "API Error",
                    "message": 'File not found: {}/{}'.format(
                        repository_name, filepath
                    )
                }, 500)
            )
        response.raise_for_status()
        return base64.standard_b64decode(response.json()['content'])

    def get_config(self, repo_name, config_filename):
        """
        Gets the specified configuration file from the specified repository.
        @params repo_name: The full name of the repository to search in the format 'owner/repo'.
        @params config_filename: The filename of the configuration file to retrieve.
        @raises APIError if the configuration file specified cannot be found.
        @returns config: A dict of the retrieved configuration for the specified repository.
        """
        config_file_contents = self.get_file_contents(repo_name, config_filename)
        config = yaml.safe_load(config_file_contents)
        return config

    def is_authorized(self, username, owner, repo, repo_config):
        """
        Validates the user against the conditions in repo config
        @params username: The username to check. Likely the review of the PR.
        @params owner: The owner of the repository.
        @params repo: The repository the PR is in.
        @params repo_config: The configuration of organizations and teams authorized to approve PRs.
        @returns boolean: True if the user has permission to approve PRs, False if not.
        """
        for org in repo_config.get("orgs", []):
            if self.is_user_in_org(org, username):
                return True
        for team in repo_config.get("teams", []):
            try:
                team_id = self.get_team_id(owner, team)
                if self.is_user_on_team(team_id, username):
                    return True
            except APIError:
                pass
        if username in repo_config.get("users", []):
            return True
        if repo_config.get("admins", False):
            repo_full_name = "{}/{}".format(owner, repo)
            return self.get_user_permission(repo_full_name, username) == 'admin'
        return False
