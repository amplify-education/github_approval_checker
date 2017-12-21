# GitHub Approval Checker
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/amplify-education/github_approval_checker/master/LICENSE)

Lambda-based GitHub webhook for overriding failed status checks on pull request approval.
# About Amplify
Amplify builds innovative and compelling digital educational products that empower teachers and students across the country. We have a long history as the leading innovator in K-12 education - and have been described as the best tech company in education and the best education company in tech. While others try to shrink the learning experience into the technology, we use technology to expand what is possible in real classrooms with real students and teachers.

Learn more at https://www.amplify.com

# Getting Started
## Prerequisites
GitHub Approval Checker requires the following to be installed:
```
python >= 2.7
npm >= 5
```

For development, `tox>=2.9.1` is recommended.

## Installing/Building

Once you've cloned the repo, run `npm install` to install dependencies from `package.json`. Python requirements from `requirements.pip` will be installed by Serverless on deploy.

## Running Tests
GitHub Approval Checker uses tox, so running `tox` will automatically execute linters as well as the unit tests. You can also run functional and integration tests by using the -e argument.

For example, `tox -e lint,py27-unit,py27-integration` will run the linters, and then the unit and integration tests in python 2.7.

To see all the available options, run `tox -l`.

## Deployment
To deploy the Approval Checker, obtain valid AWS credentials and run `serverless deploy` to deploy the lambda.

## Configuration

### Lambda Configuration
The approval checker itself requires an `environment.yml` file on deployment. An example file is included here, simply remove the `.example` extension from the file and substitute in appropriate values for each variable:


| Variable Name | Description |
| --- | --- |
| `github_username` | The GitHub username that the approval checker should query the GitHub API as. The approval checker requires access to each repository and organization it is enabled for to query team/organization membership and overwrite status messages. |
| `github_api_key` | The API key generated for the GitHub user. |
| `webhook_secret` | The secret key used to sign request webhook payloads from GitHub. |
| `config_filename` | The filename that the approval checker will look for in each repository that it is configured for. It likely makes sense to leave this value as `approval-checker-config.yml`. |

### Repository Configuration
Configuration is also required for each repository that the approval checker is enabled for, specifically:

1. ###### Webhook Configuration

    Add a webhook (found in repository -> "Settings" -> "Webhooks") for the approval checker with the following settings:


    | Field Name | Value |
    | ---------- | ----- |
    | Payload URL | `https://your-approval-checker.com/hooks/pullRequestReview` |
    | Content Type | `application/json` |
    | Secret | Same value as configured for `webhook_secret` in `environment.yml` |
    | Events | Pull Request Review |

2. ###### Repository Access Control List

    At the top-level of each repository to enable the approval checker for, include a file named `approval-checker-config.yml` (or the value set for `config_filename` in `environment.yml`) to grant approval permission based on the reviewer's membership of organizations, teams, a list of permitted users, or repository administrators. All sections are optional, but each one included should follow the format below:

    ```YAML
    orgs:
    - organization-name(s)
    teams:
    - team-slug(s)
    users:
    - username(s)
    admins: true
    ```

    | Key | Type | Default Value | Description |
    | --- | --- | --- | --- |
    | `orgs` | Sequence of strings | | Each being a GitHub organization name. |
    | `teams` | Sequence of strings | | Each being the team slug (generally the lowercase, hyphenated version of the team name) of a team belonging to the organization that owns the repository. |
    | `users` | Sequence of strings | | Each being a specific GitHub username to whitelist. |
    | `admins` | Boolean | `false` | Whether to authorize administrative users of the repository. |

# Responsible Disclosure
If you have any security issue to report, contact project maintainers privately.
You can reach us at <github@amplify.com>

# Contributing
We welcome pull requests! For your pull request to be accepted smoothly, we suggest that you:
1. For any sizable change, first open a GitHub issue to discuss your idea.
2. Create a pull request.  Explain why you want to make the change and what it’s for.
We’ll try to answer any PR’s promptly.
