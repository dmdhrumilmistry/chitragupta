from django.contrib import admin

from .models import Repo, RepoOwner, SecretScanResult, Asset, Vulnerability


@admin.register(Repo)
class RepoAdmin(admin.ModelAdmin):
    usable_fields = [
        "name",
        "owner__name",
        "platform",
        "latest_commit_sha",
        "previous_commit_sha",
        "is_fork",
        "is_private",
        "size_in_kb",
        "platform",
    ]
    search_fields = usable_fields
    list_filter = usable_fields
    list_display = usable_fields + ["created_at", "updated_at"]


@admin.register(RepoOwner)
class RepoOwnerAdmin(admin.ModelAdmin):
    search_fields = ["name", "platform", "updated_at"]
    list_filter = ["name", "platform", "updated_at"]
    list_display = ["name", "platform", "created_at", "updated_at"]


@admin.register(SecretScanResult)
class SecretScanResultAdmin(admin.ModelAdmin):
    list_filter = [
        "is_verified",
        "secret_type",
        "repo",
        "commit_datetime",
        "created_at",
        "is_false_positive",
    ]
    search_fields = ["file_path", "committer_email",
                     "secret_value"]  # removed "owner"
    list_display = [
        "file_path",
        "file_line",
        "committer_email",
        "commit_datetime",
        "is_verified",
        "repo",
        "secret_type",
        "created_at",
        "repo_owner",  # show owner via related repo
        "is_false_positive",
    ]

    def repo_owner(self, obj):
        # safe traversal: repo or repo.owner may be null
        if getattr(obj, "repo", None) and getattr(obj.repo, "owner", None):
            return getattr(obj.repo.owner, "name", None)
        return None

    repo_owner.short_description = "Owner"
    repo_owner.admin_order_field = "repo__owner__name"


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ["name", "domain", "ip",
                    "ip_version", "repo", "created_at", "updated_at"]
    search_fields = ["name", "domain", "ip",
                     "ip_version", "repo__name", "repo__owner__name"]
    list_filter = ["name", "domain", "ip",
                   "ip_version", "repo__name", "repo__owner__name"]


@admin.register(Vulnerability)
class VulnerabilityAdmin(admin.ModelAdmin):
    list_display = ["created_at", "updated_at", "file_path", "asset", "source", "external_id", "title", "description", "severity",
                    "state", "line_number", "package_name", "affected_version", "fixed_version", "cvss_score", "cvss_vector", "last_seen_at"]
    search_fields = ["file_path", "asset__name", "asset__domain", "asset__ip",
                     "asset__ip_version", "asset__repo__name", "asset__repo__owner__name"]
    list_filter = ["file_path", "asset__name", "asset__domain", "asset__ip",
                   "asset__ip_version", "asset__repo__name", "asset__repo__owner__name", "severity"]
