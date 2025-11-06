from datetime import datetime
from github import Github
from github.PaginatedList import PaginatedList
from github.Repository import Repository
from github.Commit import Commit
from github.Auth import AppAuth


class GitHubUtils:
    def __init__(self, github_app_id: str, app_private_key: str, installation_id:int):
        self.app_auth = AppAuth(github_app_id, app_private_key)
        self.auth = self.app_auth.get_installation_auth(installation_id)
        self.client = Github(auth=self.auth)

    def get_owner_repos(self, owner: str) -> PaginatedList[Repository]:
        return self.client.get_user(owner).get_repos()
    


if __name__ == "__main__":
    from django.conf import settings
    default_config = settings.GITHUB_APPS_CONFIG.get("default")
    gh = GitHubUtils(
        github_app_id=default_config["client_id"],
        app_private_key=default_config["private_key"],
        installation_id=int(default_config["installation_id"]),
    )
    
    until = datetime.now()
    for repo in gh.get_owner_repos("dmdhrumilmistry"):
        commit_details = repo.get_commits(until=until)
        commit_date = commit_details[0]._rawData.get('commit',{}).get('author',{}).get('date')

    