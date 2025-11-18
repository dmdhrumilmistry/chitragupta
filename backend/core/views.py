from rest_framework.schemas import get_schema_view
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.viewsets import ModelViewSet
# from rest_framework import permissions

from .models import RepoOwner, Repo
from .serializers import RepoOwnerSerializer, RepoSerializer
from .mixins import FilteredCacheMixin


schema_view = get_schema_view(
    title="Chitragupta API",
    # url="https://www.example.org/api/",
    renderer_classes=[JSONOpenAPIRenderer],
)


class RepoOwnerViewSet(FilteredCacheMixin, ModelViewSet):
    queryset = RepoOwner.objects.all()
    serializer_class = RepoOwnerSerializer
    filterset_fields = ["platform", "name"]
    cache_filters = ["platform", "name"]
    cache_version_key = "repoowner_version"


class RepoViewSet(FilteredCacheMixin, ModelViewSet):
    queryset = Repo.objects.all()
    serializer_class = RepoSerializer
    filterset_fields = ["owner__name", "platform", "is_private", "is_fork"]
    cache_filters = ["owner__name", "platform", "is_private", "is_fork"]
    cache_version_key = "repo_version"