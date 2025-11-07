from logging import getLogger

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import RepoOwner
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
