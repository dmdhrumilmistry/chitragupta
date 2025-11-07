from datetime import datetime
from logging import getLogger

from celery import shared_task
from django.conf import settings

from core.models import RepoOwner, Repo
from utils.github import GitHubUtils

logger = getLogger(__name__)


@shared_task
def fetch_owner_repos_task(instance_pk: str):
    try:
        owner = RepoOwner.objects.get(pk=instance_pk)
        logger.info(f"Fetched RepoOwner: {owner}")
    except RepoOwner.DoesNotExist:
        return {"ok": False, "reason": "instance_not_found"}

    default_config = settings.GITHUB_APPS_CONFIG.get("default")
    gh = GitHubUtils(
        github_app_id=default_config["client_id"],
        app_private_key=default_config["private_key"],
        installation_id=int(default_config["installation_id"]),
    )

    # until = datetime.now()
    for repo in gh.get_owner_repos(owner.name):
        try:
            obj, created = Repo.objects.get_or_create(
                https_url=repo.clone_url,
                ssh_url=repo.ssh_url,
                owner=owner,
                name=repo.name,
                defaults={
                    "is_fork": repo.fork,
                    "is_private": repo.private == "private",
                    "size_in_kb": repo.size,
                    "platform": owner.platform,
                },
            )
            if created:
                logger.info(f"Created repo: {repo.full_name}")
            else:
                logger.info(f"Repo already exists with id {obj.id}: {repo.full_name}")
        except Exception:
            logger.error(f"Error creating repo {repo.full_name}", exc_info=True)

        # commit_details = repo.get_commits(until=until)
        # process commit_details...
    return {"ok": True}
