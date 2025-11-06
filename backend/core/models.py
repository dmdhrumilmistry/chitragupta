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
    previous_commit_sha = models.CharField(max_length=40, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.platform}({self.owner.name}/{self.name}@{self.latest_commit_sha})"

