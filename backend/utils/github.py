"""
This module contains utilities for GitHub integration.
"""
from django.conf import settings

from github import Github
from github.DependabotAlert import DependabotAlert
from github.Organization import Organization
from github.NamedUser import NamedUser
from github.PaginatedList import PaginatedList
from github.Repository import Repository
from github.Auth import AppAuth
from github.Commit import Commit


def get_github_app(config_name: str = "default"):
    """
    Returns a GitHubUtils instance for the default GitHub app.
    """
    default_config = settings.GITHUB_APPS_CONFIG.get(config_name)
    return GitHubUtils(
        github_app_id=default_config["app_id"],
        app_private_key=default_config["private_key"],
        installation_id=int(default_config["installation_id"]),
    )


class GitHubUtils:
    """
    Utility class for GitHub App integration.
    """

    def __init__(self, github_app_id: str, app_private_key: str, installation_id: int):
        """
        Initializes the GitHubUtils instance.
        """
        self.app_auth = AppAuth(github_app_id, app_private_key)
        self.auth = self.app_auth.get_installation_auth(installation_id)
        self.client: Github = Github(auth=self.auth)

    def get_owner_repos(self, owner: str) -> PaginatedList[Repository]:
        """
        Fetches all repositories for a user or organization.
        """
        return self.client.get_user(owner).get_repos()

    def get_org_users(self, org_name: str) -> PaginatedList[NamedUser]:
        """
        Fetches all users for an organization.
        """
        org: Organization = self.client.get_organization(org_name)
        return org.get_members()

    def get_org_repos(self, org_name: str) -> PaginatedList[Repository]:
        """
        Fetches all repositories for an organization.
        """
        org: Organization = self.client.get_organization(org_name)
        return org.get_repos()

    def get_repo_alerts(self, repo: Repository, state=None, severity=None, **kwargs) -> PaginatedList[DependabotAlert]:
        """
        Fetches dependabot alerts for a repository.
        """
        if not state:
            state = ["open"]
        if not severity:
            severity = ["low", "medium", "high", "critical"]
        return repo.get_dependabot_alerts(state=state, severity=severity, **kwargs)


# if __name__ == "__main__":
#     from datetime import datetime
#     from github.Commit import Commit

#     default_config = settings.GITHUB_APPS_CONFIG.get("default")
#     gh = GitHubUtils(
#         github_app_id=default_config["client_id"],
#         app_private_key=default_config["private_key"],
#         installation_id=int(default_config["installation_id"]),
#     )

#     until = datetime.now()
#     for repo in gh.get_owner_repos("dmdhrumilmistry"):
#         commit_details = repo.get_commits(until=until)
#         commit_date = commit_details[0]._rawData.get(
#             'commit', {}).get('author', {}).get('date')
