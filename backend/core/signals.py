from logging import getLogger

from django.db.models.signals import pre_save, post_save, post_delete
from django.core.cache import cache
from django.dispatch import receiver

from .models import RepoOwner, Repo, Asset
from .tasks import fetch_owner_repos_task

logger = getLogger(__name__)


@receiver(post_save, sender=RepoOwner)
def repo_owner_post_save(sender, instance: RepoOwner, created, **kwargs):
    """
    Runs after a RepoOwner is saved.
    """
    if created and instance.platform == "github":
        fetch_owner_repos_task.delay(str(instance.pk))


@receiver(post_save, sender=Repo)
def repo_post_save(sender, instance: Repo, created, **kwargs):
    """
    Runs after a Repo is saved.
    """
    try:
        if created:
            asset, created = Asset.objects.get_or_create(  # pylint: disable=no-member
                repo=instance,
                name=instance.name,
                domain=instance.https_url,
            )
            if created:
                logger.info("Created asset for repo: %s", asset)
            else:
                logger.info("Asset already exists for repo: %s", asset)
    except Exception:  # pylint: disable=broad-except
        logger.error("Error creating asset for repo %s",
                     instance, exc_info=True)


@receiver([post_save, post_delete], sender=Repo)
def bump_repo_version(sender, instance, **kwargs):
    try:
        cache.incr("repo_version")
    except Exception:
        # set a timestamp fallback
        cache.set("repo_version", str(instance.updated_at.isoformat()
                  if hasattr(instance, "updated_at") else ""), None)


@receiver([post_save, post_delete], sender=RepoOwner)
def bump_repoowner_version(sender, instance, **kwargs):
    try:
        cache.incr("repoowner_version")
    except Exception:
        cache.set("repoowner_version", str(instance.updated_at.isoformat()
                  if hasattr(instance, "updated_at") else ""), None)
