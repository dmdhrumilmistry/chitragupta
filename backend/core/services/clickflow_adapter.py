import os
from clickflow_sync import ClickFlowEngine, ClickUpTask, SlackPlugin

engine = ClickFlowEngine()
slack = SlackPlugin()

def build_task_from_secret(secret):
    title = f"Secret found: {secret.type or 'Unknown'} in {secret.repo_name}"
    description = (
        f"Repository: {secret.repo_name}\n"
        f"Path: {secret.file_path}\n"
        f"Commit: {getattr(secret, 'commit_sha', '')}\n"
        f"Detector: Trufflehog\n"
        f"Status: {'Verified' if secret.verified else 'Unverified'}\n"
    )
    internal_id = f"SEC-{secret.id}"  # stable, idempotent reference
    priority = 2 if secret.verified else 3
    tags = ["secret", "trufflehog", secret.repo_name]
    return ClickUpTask(
        internal_id=internal_id,
        title=title,
        description=description,
        priority=priority,
        tags=tags,
    )

def upsert_secret_task(secret):
    task = build_task_from_secret(secret)
    # Slack callback can be disabled if not configured
    callback = slack.send_notification if os.getenv("SLACK_WEBHOOK_URL") else None
    engine.upsert_task(task, callback=callback)

def build_task_from_vuln(vuln):
    title = f"Vulnerability: {vuln.title or vuln.type} in {vuln.repo_name}"
    description = (
        f"Repository: {vuln.repo_name}\n"
        f"Path: {getattr(vuln, 'file_path', '')}\n"
        f"Severity: {getattr(vuln, 'severity', 'unknown')}\n"
        f"Status: {getattr(vuln, 'status', 'open')}\n"
    )
    internal_id = f"VULN-{vuln.id}"
    sev = (getattr(vuln, 'severity', '') or '').lower()
    priority = 1 if sev in ("critical", "high") else 3
    tags = ["vulnerability", sev, vuln.repo_name]
    return ClickUpTask(
        internal_id=internal_id,
        title=title,
        description=description,
        priority=priority,
        tags=tags,
    )

def upsert_vuln_task(vuln):
    task = build_task_from_vuln(vuln)
    callback = slack.send_notification if os.getenv("SLACK_WEBHOOK_URL") else None
    engine.upsert_task(task, callback=callback)
