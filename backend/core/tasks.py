"""
This module contains tasks used throughout the application.
"""

from datetime import datetime
from json import loads, JSONDecodeError
from logging import getLogger
from subprocess import run, PIPE, STDOUT

from dateutil import parser
from celery import shared_task

from core.models import RepoOwner, Repo, SecretScanResult
from core.exceptions import TrufflehogScanError
from utils.github import GitHubUtils, get_default_github_app

logger = getLogger(__name__)


@shared_task
def fetch_owner_repos_task(instance_pk: str):
    """
    Fetches all repositories for a user or organization.
    """
    try:
        owner = RepoOwner.objects.get(  # pylint: disable=no-member
            pk=instance_pk)
        logger.info("Fetched RepoOwner: %s", owner)
    except RepoOwner.DoesNotExist:  # pylint: disable=no-member
        return {"ok": False, "reason": "instance_not_found"}

    gh: GitHubUtils = get_default_github_app()

    # until = datetime.now()
    for repo in gh.get_owner_repos(owner.name):
        try:
            obj, created = Repo.objects.get_or_create(  # pylint: disable=no-member
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
                logger.info("Created repo: %s", repo.full_name)
            else:
                logger.info(
                    "Repo already exists with id %s: %s", str(obj.id), repo.full_name)
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "Error creating repo %s", repo.full_name, exc_info=True)
        # commit_details = repo.get_commits(until=until)
        # process commit_details...
    return {"ok": True}


@shared_task
def scan_repo(repo_pk: str, concurrency: int = 10, only_verified: bool = False):
    """
    Triggers Trufflehog scan for a repository.
    """
    try:
        repo = Repo.objects.get(pk=repo_pk)  # pylint: disable=no-member
    except Repo.DoesNotExist:  # pylint: disable=no-member
        logger.error("Repo with pk %s does not exist.", repo_pk)
        return {"ok": False, "reason": "repo_not_found"}

    gh = get_default_github_app()
    token = gh.auth.token

    until = datetime.now()
    command = [
        "trufflehog",
        "git",
        repo.get_https_clone_url(token=token),
        f"--concurrency={concurrency}",
        "--json",
        "--no-update",
        "--user-agent-suffix=ChitraGupta",
    ]

    if repo.latest_commit_sha != "":
        command.append(f"--since-commit={repo.latest_commit_sha}")

    if only_verified:
        command.append("--only-verified")

    logger.info(
        "Scanning repository: %s with command: %s",
        repo,
        " ".join(command),
    )
    try:
        trufflehog_output = run(
            command,
            stdout=PIPE,
            stderr=STDOUT,
            text=True,
            check=True,
        )

        logger.info(
            "Trufflehog scan completed for repo %s: %s",
            repo.https_url,
            trufflehog_output.stdout,
        )
        if "encountered errors during scan" in trufflehog_output.stdout:
            raise TrufflehogScanError(
                f"Trufflehog scan failed for repo {repo.https_url}, "
                f"error: {trufflehog_output.stdout}"
            )

        # Process trufflehog_output.stdout to extract secrets
        for line in trufflehog_output.stdout.splitlines():
            if not line.strip():
                continue

            if "SourceMetadata" not in line:
                continue

            try:
                result_data = loads(line)
                git_data = result_data.get("SourceMetadata", {}).get(
                    "Data", {}).get("Git", {})

                commit_timestamp = git_data.get("timestamp")
                commit_datetime = parser.parse(commit_timestamp)

                secret_result, created = SecretScanResult.objects.get_or_create(  # pylint: disable=no-member
                    file_path=git_data.get("file"),
                    file_line=git_data.get("line"),
                    committer_email=git_data.get("email"),
                    commit_datetime=commit_datetime,
                    is_verified=result_data.get("Verified", False),
                    repo=repo,
                    secret_type=result_data.get("DetectorName", ""),
                    secret_value=result_data.get("Raw", ""),
                    secret_value_rawv2=result_data.get("RawV2", ""),
                    additional_info=result_data,
                )

                if created:
                    logger.info("Created SecretScanResult: %s", secret_result)
                else:
                    logger.info(
                        "SecretScanResult already exists: %s", secret_result)

            except JSONDecodeError:
                logger.warning("Failed to decode JSON line: %s", line)
            except Exception:  # pylint: disable=broad-except
                logger.error(
                    "Error saving SecretScanResult from line: %s",
                    line,
                    exc_info=True
                )

        # update repo commit SHAs if scan was successful
        repo.previous_commit_sha = repo.latest_commit_sha
        repo.latest_commit_sha = (
            gh.client.get_repo(f"{repo.owner.name}/{repo.name}", lazy=True)
            .get_commits(until=until)[0]
            .sha
        )
        repo.save()

    except Exception:  # pylint: disable=broad-except
        logger.error(
            "Error scanning repo %s with command: %s",
            repo,
            command,
            exc_info=True
        )
        return {"ok": False, "reason": "scan_error"}

    return {"ok": True}


@shared_task(bind=True)
def sync_github_org_users(self):  # pylint: disable=unused-argument
    """
    Sync GitHub organization users.
    """
    organizations = RepoOwner.objects.filter(  # pylint: disable=no-member
        is_organization=True)

    gh: GitHubUtils = get_default_github_app()
    for org in organizations:
        if org.platform != "github":
            logger.info("Skipping non-GitHub organization: %s", org.name)
            continue

        for member in gh.get_org_users(org.name):
            try:
                owner, created = RepoOwner.objects.get_or_create(  # pylint: disable=no-member
                    name=member.login,
                    is_organization=False,
                    platform=org.platform,
                )

                if created:
                    logger.info(
                        "Created RepoOwner for user %s: %s",
                        member.login,
                        owner.id
                    )
                else:
                    logger.info(
                        "RepoOwner already exists for user %s: %s",
                        member.login,
                        owner.id
                    )
            except Exception:  # pylint: disable=broad-except
                logger.error(
                    "Error creating RepoOwner for user %s",
                    member.login,
                    exc_info=True
                )

    return {"ok": True}


@shared_task(bind=True)
def trigger_trufflehog_scan_for_all_repos(
    self,  # pylint: disable=unused-argument
    concurrency: int = 10,
    only_verified: bool = False
):
    """
    Trigger Trufflehog scan for all repositories.
    """
    repos = Repo.objects.all()  # pylint: disable=no-member
    total_repos = repos.count()
    for index, repo in enumerate(repos):
        logger.info(
            "Triggering scan for repo %s (%s/%s)",
            repo,
            index + 1,
            total_repos
        )
        scan_repo.delay(
            str(repo.pk),
            concurrency=concurrency,
            only_verified=only_verified
        )
    return {"ok": True, "total_repos_triggered": total_repos}


@shared_task(bind=True)
def sync_user_repos(self):  # pylint: disable=unused-argument
    """
    Syncs all repositories for a user.
    """
    users = RepoOwner.objects.filter(  # pylint: disable=no-member
        is_organization=False)

    total_users = users.count()
    for index, user in enumerate(users):
        logger.info(
            "Syncing repos for user %s (%s/%s)",
            user,
            index + 1,
            total_users
        )
        fetch_owner_repos_task.delay(str(user.pk))

    return {"ok": True, "total_users_triggered": total_users}
