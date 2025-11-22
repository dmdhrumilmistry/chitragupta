from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField

repo_platform_choices = [
    ("github", "GitHub"),
    # ("gitlab", "GitLab"),
    # ("bitbucket", "Bitbucket"),
]


class RepoOwner(models.Model):
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
        return f"{self.platform}({self.name})"


class Repo(models.Model):
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
