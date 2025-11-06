from rest_framework.schemas import get_schema_view
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.decorators import action
from rest_framework.response import Response

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .models import RepoOwner, Repo
from .serializers import RepoOwnerSerializer, RepoSerializer


schema_view = get_schema_view(
    title="Chitragupta API",
    # url="https://www.example.org/api/",
    renderer_classes=[JSONOpenAPIRenderer],
)


@method_decorator(cache_page(60 * 15), name='dispatch')
class RepoOwnerViewSet(ModelViewSet):
    queryset = RepoOwner.objects.all()
    serializer_class = RepoOwnerSerializer
    filterset_fields = ['platform', 'name']

@method_decorator(cache_page(60 * 15), name='dispatch')
class RepoViewSet(ModelViewSet):
    queryset = Repo.objects.all()
    serializer_class = RepoSerializer
    filterset_fields = ['owner__name', 'platform', 'is_private', 'is_fork']