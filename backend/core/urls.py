"""
Core URLs for Chitragupta API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    schema_view,
    RepoOwnerViewSet,
    RepoViewSet,
    TriggerTaskView,
    SecretScanResultViewSet,
)

router = DefaultRouter()
router.register(r"repo-owners", RepoOwnerViewSet, basename="repo_owners")
router.register(r"repos", RepoViewSet, basename="repos")
router.register(r"secret-scan-results", SecretScanResultViewSet,
                basename="secret_scan_results")

urlpatterns = [
    path("schema.json", schema_view),
    path("trigger-task/", TriggerTaskView.as_view(), name="trigger_task"),
    path("", include(router.urls)),
]
