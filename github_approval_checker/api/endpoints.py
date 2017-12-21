"""
Represents all endpoints exposed for the API. Each is prefixed by its
appropriate HTTP verb.
"""

import os
import logging
import connexion
from github_approval_checker.utils import util
from github_approval_checker.utils import logging_config
from github_approval_checker.utils.github_handler import GithubHandler
from github_approval_checker.utils.exceptions import ConfigError, APIError, SignatureError

logging_config.configure_logging(False, False)
logger = logging.getLogger(__name__)


def post_pull_request_review(data):
    """
    Receive a webhook event of type PullRequestReview
    @params data: Request json passed in from GitHub
    @return: Returns 200 to indicate that status was posted successfully
    or returns an Error message.
    """

    try:
        signature = util.parse_signature(connexion.request.headers.get('X-Hub-Signature', ''))

        util.verify_signature(
            connexion.request.data,
            signature,
            os.getenv('webhook_secret')
        )
    except SignatureError as err:
        logger.error(err.message)
        return err.response

    api_handler = GithubHandler(os.getenv('github_username'), os.getenv('github_api_key'))

    repo = data['repository']['name']
    organization = data['repository']['owner']['login']
    repo_full_name = data['repository']['full_name']

    reviewer = data['review']['user']['login']
    review_state = data['review']['state']
    review_ref = data['review']['commit_id']

    try:
        repo_config = api_handler.get_config(repo_full_name, os.getenv('config_filename'))
    except APIError as err:
        logger.error("Configuration file error: " + err.message)
        return err.response

    try:
        util.validate_config(repo_config)
    except ConfigError as err:
        logger.error("Configuration validation error: " + err.message)
        return err.response

    # Check that the review was 'approved' and not changes reqeusted or something else
    if review_state != 'approved':
        logger.info('Review was not approved. Nothing overwritten.')
        return ({'status': 'OK', 'message': 'Review state is not approved'}, 200)

    # Get the current status messages on the PR
    status_messages = api_handler.get_statuses(repo_full_name, review_ref)

    for status in status_messages:
        if (status['state'] in ['error', 'failure'] and
                api_handler.is_authorized(reviewer, organization, repo, repo_config)):
            logger.info(
                "%s is authorized to overwrite failed status in repository %s", reviewer, repo
            )
            res_status_code = api_handler.post_status(
                repo_full_name,
                review_ref,
                status['context'],
                status['target_url'],
                reviewer,
                status['description']
            )
            if res_status_code == 201:
                logger.info('Successfully posted a status')
            else:
                logger.error('Failed to post a status to Github for an approved reivew.')

    return util.STATUS_OK
