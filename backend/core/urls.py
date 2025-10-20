from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import schema_view, RepoOwnerViewSet, RepoViewSet

router = DefaultRouter()
router.register(r"repo-owners", RepoOwnerViewSet, basename="repo_owners")
router.register(r"repos", RepoViewSet, basename="repos")

urlpatterns = [
    path("schema.json", schema_view),
    path("", include(router.urls)),
]

