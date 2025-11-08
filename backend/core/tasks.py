from datetime import datetime
from dateutil import parser
from json import loads, JSONDecodeError
from logging import getLogger
from subprocess import run, PIPE, STDOUT

from celery import shared_task

from core.models import RepoOwner, Repo, SecretScanResult
from utils.github import GitHubUtils, get_default_github_app

logger = getLogger(__name__)


@shared_task
def fetch_owner_repos_task(instance_pk: str):
    try:
        owner = RepoOwner.objects.get(pk=instance_pk)
        logger.info(f"Fetched RepoOwner: {owner}")
    except RepoOwner.DoesNotExist:
        return {"ok": False, "reason": "instance_not_found"}

    gh: GitHubUtils = get_default_github_app()

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


@shared_task
def scan_repo(repo_pk: str, concurrency: int = 10, only_verified: bool = False):
    try:
        repo = Repo.objects.get(pk=repo_pk)
    except Repo.DoesNotExist:
        logger.error(f"Repo with pk {repo_pk} does not exist.")
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

    # Placeholder for scanning logic
    logger.info(f"Scanning repository: {repo} with command: {' '.join(command)}")
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
            raise Exception(
                f"Trufflehog scan failed for repo {repo.https_url}, error: {trufflehog_output.stdout}"
            )

        # Process trufflehog_output.stdout to extract secrets
        for line in trufflehog_output.stdout.splitlines():
            if not line.strip():
                continue

            if "SourceMetadata" not in line:
                continue

            try:
                result_data = loads(line)
                git_data = result_data.get("SourceMetadata", {}).get("Data", {}).get("Git", {})
                
                commit_timestamp = git_data.get("timestamp")
                commit_datetime = parser.parse(commit_timestamp)

                secret_result, created = SecretScanResult.objects.get_or_create(
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
                    logger.info(f"Created SecretScanResult: {secret_result}")
                else:
                    logger.info(f"SecretScanResult already exists: {secret_result}")
                
            except JSONDecodeError:
                logger.warning(f"Failed to decode JSON line: {line}")
            except Exception:
                logger.error(
                    f"Error saving SecretScanResult from line: {line}", exc_info=True
                )

        # update repo commit SHAs if scan was successful
        repo.previous_commit_sha = repo.latest_commit_sha
        repo.latest_commit_sha = (
            gh.client.get_repo(f"{repo.owner.name}/{repo.name}", lazy=True)
            .get_commits(until=until)[0]
            .sha
        )
        repo.save()

    except Exception:
        logger.error(
            f"Error scanning repo {repo} with command: {command}", exc_info=True
        )
        return {"ok": False, "reason": "scan_error"}

    return {"ok": True}

@shared_task(bind=True)
def sync_github_org_users():
    organizations = RepoOwner.objects.filter(is_organization=True)
    
    gh: GitHubUtils = get_default_github_app()
    for org in organizations:
        if org.platform != "github":
            logger.info(f"Skipping non-GitHub organization: {org.name}")
            continue

        for member in gh.get_org_users(org.name):
            try:
                owner, created = RepoOwner.objects.get_or_create(
                    name=member.login,
                    is_organization=False,
                    platform=org.platform,
                )

                if created:
                    logger.info(f"Created RepoOwner for user {member.login}: {owner.id}")
                else:
                    logger.info(f"RepoOwner already exists for user {member.login}: {owner.id}")
            except Exception:
                logger.error(f"Error creating RepoOwner for user {member.login}", exc_info=True)

    return {"ok": True}

@shared_task(bind=True)
def trigger_trufflehog_scan_for_all_repos(self, concurrency: int = 10, only_verified: bool = False):
    repos = Repo.objects.all()
    total_repos = repos.count()
    for index, repo in enumerate(repos):
        logger.info(f"Triggering scan for repo {repo} ({index + 1}/{total_repos})")
        scan_repo.delay(repo.pk, concurrency=concurrency, only_verified=only_verified)
    return {"ok": True, "total_repos_triggered": total_repos}
