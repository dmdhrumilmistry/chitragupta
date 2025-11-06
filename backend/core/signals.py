from datetime import datetime
from logging import getLogger

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.conf import settings
from .models import RepoOwner, Repo

logger = getLogger(__name__)

from utils.github import GitHubUtils


# @receiver(pre_save, sender=RepoOwner)
# def repo_owner_pre_save(sender, instance: RepoOwner, **kwargs):
#     """
#     Runs before a RepoOwner is saved. Attach previous values on the instance
#     so post_save can compare them.
#     """
#     # new object being created
#     if not instance.pk:
#         instance._previous_state = None
#         return


# TODO: move this to celery in future
@receiver(post_save, sender=RepoOwner)
def repo_owner_post_save(sender, instance: RepoOwner, created, **kwargs):
    """
    Runs after a RepoOwner is saved.
    """
    if created:
        if instance.platform == "github":
            default_config = settings.GITHUB_APPS_CONFIG.get("default")
            gh = GitHubUtils(
                github_app_id=default_config["client_id"],
                app_private_key=default_config["private_key"],
                installation_id=int(default_config["installation_id"]),
            )

            for repo in gh.get_owner_repos(instance.name):
                try:
                    Repo.objects.create(
                        https_url=repo.clone_url,
                        ssh_url=repo.ssh_url,
                        owner=instance,
                        name=repo.name,
                        is_fork=repo.fork,
                        is_private=repo.private == "private",
                        size_in_kb=repo.size,
                        platform=instance.platform,
                    )
                    logger.info(f"Created repo: {repo.full_name}")
                except Exception:
                    logger.error(f"Error creating repo {repo.full_name}", exc_info=True)
