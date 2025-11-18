from logging import getLogger

from django.db.models.signals import pre_save, post_save, post_delete
from django.core.cache import cache
from django.dispatch import receiver

from .models import RepoOwner, Repo
from .tasks import fetch_owner_repos_task

logger = getLogger(__name__)


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


@receiver(post_save, sender=RepoOwner)
def repo_owner_post_save(sender, instance: RepoOwner, created, **kwargs):
    """
    Runs after a RepoOwner is saved.
    """
    if created and instance.platform == "github":
        fetch_owner_repos_task.delay(str(instance.pk))

@receiver([post_save, post_delete], sender=Repo)
def bump_repo_version(sender, instance, **kwargs):
    try:
        cache.incr("repo_version")
    except Exception:
        # set a timestamp fallback
        cache.set("repo_version", str(instance.updated_at.isoformat() if hasattr(instance, "updated_at") else ""), None)

@receiver([post_save, post_delete], sender=RepoOwner)
def bump_repoowner_version(sender, instance, **kwargs):
    try:
        cache.incr("repoowner_version")
    except Exception:
        cache.set("repoowner_version", str(instance.updated_at.isoformat() if hasattr(instance, "updated_at") else ""), None)