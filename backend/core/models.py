from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField

repo_platform_choices = [
    ("github", "GitHub"),
    # ("gitlab", "GitLab"),
    # ("bitbucket", "Bitbucket"),
]


class Asset(models.Model):
    """
    This model represents an asset.
    """
    id = ObjectIdAutoField(primary_key=True)
    name = models.CharField(max_length=150)
    domain = models.CharField(max_length=255)
    ip = models.GenericIPAddressField(null=True, blank=True)
    ip_version = models.CharField(max_length=10, null=True, blank=True, choices=[
        ("ipv4", "IPv4"),
        ("ipv6", "IPv6"),
    ])
    status = models.CharField(max_length=30, choices=[
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("deprecated", "Deprecated"),
    ], default="active")
    repo = models.ForeignKey(
        "Repo", on_delete=models.CASCADE, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Asset({self.name})"


class RepoOwner(models.Model):
    """
    This model represents a repository owner.
    """
    id = ObjectIdAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    platform = models.CharField(
        max_length=100,
        choices=repo_platform_choices,
        default="github",
    )
    is_organization = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"RepoOwner({self.platform}({self.name})"


class Repo(models.Model):
    """
    This model represents a repository.
    """
    id = ObjectIdAutoField(primary_key=True)
    https_url = models.URLField(unique=True)
    ssh_url = models.URLField(unique=True)
    owner = models.ForeignKey(RepoOwner, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    is_fork = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    size_in_kb = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    platform = models.CharField(
        max_length=100,
        choices=repo_platform_choices,
        default="github",
    )
    latest_commit_sha = models.CharField(max_length=40)
    previous_commit_sha = models.CharField(
        max_length=40, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.platform}({self.owner.name}/{self.name}@{self.latest_commit_sha})"
        )

    def get_https_clone_url(self, token: str):
        if self.platform == "github" and self.is_private:
            return f"https://x-access-token:{token}@{self.owner.name}/{self.name}.git"

        return self.https_url


class SecretScanResult(models.Model):
    """
    This model represents a secret scan result.
    """
    id = ObjectIdAutoField(primary_key=True)
    file_path = models.CharField(max_length=500)
    file_line = models.IntegerField(null=True, blank=True)
    committer_email = models.TextField(null=True, blank=True)
    commit_datetime = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    repo = models.ForeignKey(
        Repo, on_delete=models.CASCADE, null=True, blank=True)

    secret_type = models.CharField(max_length=100)
    secret_value = models.TextField()
    secret_value_rawv2 = models.TextField(null=True, blank=True)

    additional_info = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_rotated = models.BooleanField(default=False)
    rotated_at = models.DateTimeField(null=True, blank=True)

    is_false_positive = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"SecretScanResult({self.file_path}, {self.secret_type})"


class Vulnerability(models.Model):
    """
    This model represents a vulnerability found in an asset.
    """
    id = ObjectIdAutoField(primary_key=True)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)

    # Source info
    source = models.CharField(max_length=100)  # e.g., "dependabot", "codeql"
    # e.g., alert number or unique identifier from source
    external_id = models.CharField(max_length=100)

    # Core vulnerability info
    title = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)
    severity = models.CharField(max_length=20, choices=[
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
        ("info", "Informational"),
        ("unknown", "Unknown"),
    ], default="unknown")

    state = models.CharField(max_length=20, choices=[
        ("open", "Open"),
        ("fixed", "Fixed"),
        ("dismissed", "Dismissed"),
        ("auto_dismissed", "Auto Dismissed"),
        ("false_positive", "False Positive"),
        ("rotated", "Rotated"),
        ("in_progress", "In Progress"),
        ("accepted_risk", "Accepted Risk")
    ], default="open")

    # Additional context
    file_path = models.CharField(max_length=500, null=True, blank=True)
    line_number = models.IntegerField(null=True, blank=True)

    # For dependency vulnerabilities
    package_name = models.CharField(max_length=200, null=True, blank=True)
    affected_version = models.CharField(max_length=100, null=True, blank=True)
    fixed_version = models.CharField(max_length=100, null=True, blank=True)

    # Vuln metadata
    ghsa_id = models.CharField(max_length=100, null=True, blank=True)
    cve_ids = models.JSONField(null=True, blank=True)
    cwe_ids = models.JSONField(null=True, blank=True)
    cvss_score = models.FloatField(null=True, blank=True)
    cvss_vector = models.CharField(max_length=200, null=True, blank=True)
    references = models.JSONField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen_at = models.DateTimeField(auto_now_add=True)

    # Store full raw data for future proofing
    raw_data = models.JSONField(null=True, blank=True)

    class Meta:
        unique_together = ("asset", "source", "external_id")
        ordering = ["-created_at"]
        verbose_name_plural = "Vulnerabilities"

    def __str__(self):
        return f"{self.source}:{self.external_id} - {self.title}"
