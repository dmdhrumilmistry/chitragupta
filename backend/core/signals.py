from logging import getLogger

from django.db.models.signals import pre_save, post_save, post_delete
from django.core.cache import cache
from django.dispatch import receiver

from .models import RepoOwner, Repo, Asset, Vulnerability, SecretScanResult
from .tasks import fetch_owner_repos_task

from .services.clickflow_adapter import upsert_secret_task, upsert_vuln_task

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


@receiver(post_save, sender=SecretFinding)
def secret_post_save(sender, instance, created, **kwargs):
    # Sync on create or when verification toggles
    should_sync = created or (instance.tracker.has_changed('verified') if hasattr(instance, 'tracker') else True)
    if should_sync:
        upsert_secret_task(instance)

@receiver(post_save, sender=Vulnerability)
def vuln_post_save(sender, instance, created, **kwargs):
    # Sync on create or material status/severity changes
    changed = False
    if hasattr(instance, 'tracker'):
        for field in ('status', 'severity', 'title'):
            changed = changed or instance.tracker.has_changed(field)
    if created or changed:
        upsert_vuln_task(instance)
