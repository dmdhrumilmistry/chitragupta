"""
Core views for Chitragupta API.
"""

from logging import getLogger

from rest_framework.schemas import get_schema_view
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


from .mixins import FilteredCacheMixin
from .serializers import RepoOwnerSerializer, RepoSerializer, SecretScanResultSerializer
from .models import RepoOwner, Repo, SecretScanResult
from .tasks import (
    fetch_owner_repos_task,
    scan_repo,
    sync_github_org_users,
    trigger_trufflehog_scan_for_all_repos,
    sync_user_repos,
)

logger = getLogger(__name__)


schema_view = get_schema_view(
    title="Chitragupta API",
    # url="https://www.example.org/api/",
    renderer_classes=[JSONOpenAPIRenderer],
)


class RepoOwnerViewSet(FilteredCacheMixin, ModelViewSet):
    """
    ViewSet for managing RepoOwner objects.
    """
    queryset = RepoOwner.objects.all()  # pylint: disable=no-member
    serializer_class = RepoOwnerSerializer
    filterset_fields = ["platform", "name"]
    cache_filters = ["platform", "name"]
    cache_version_key = "repoowner_version"


class RepoViewSet(FilteredCacheMixin, ModelViewSet):
    """
    ViewSet for managing Repo objects.
    """
    queryset = Repo.objects.all()  # pylint: disable=no-member
    serializer_class = RepoSerializer
    filterset_fields = ["owner__name", "platform", "is_private", "is_fork"]
    cache_filters = ["owner__name", "platform", "is_private", "is_fork"]
    cache_version_key = "repo_version"


class SecretScanResultViewSet(FilteredCacheMixin, ModelViewSet):
    """
    ViewSet for managing SecretScanResult objects.
    """
    queryset = SecretScanResult.objects.all()  # pylint: disable=no-member
    serializer_class = SecretScanResultSerializer
    filterset_fields = ["repo__name", "platform", "is_private", "is_fork"]
    cache_filters = ["repo__name", "platform", "is_private", "is_fork"]
    cache_version_key = "secretscanresult_version"


class TriggerTaskView(APIView):
    """
    View for triggering Celery tasks.
    """
    permission_classes = [IsAdminUser]

    ALLOWED_TASKS = {
        "fetch_owner_repos_task": fetch_owner_repos_task,
        "scan_repo": scan_repo,
        "sync_github_org_users": sync_github_org_users,
        "trigger_trufflehog_scan_for_all_repos": trigger_trufflehog_scan_for_all_repos,
        "sync_user_repos": sync_user_repos,
    }

    @method_decorator(csrf_exempt, name='dispatch')
    def post(self, request):
        """
        Trigger a Celery task based on the provided task name and arguments.
        """
        task_name = request.data.get("task_name")
        args = request.data.get("args", [])
        kwargs = request.data.get("kwargs", {})

        if task_name not in self.ALLOWED_TASKS:
            return Response(
                {"error": f"Task '{task_name}' is not allowed or does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task_func = self.ALLOWED_TASKS[task_name]

        try:
            # Trigger the task asynchronously
            result = task_func.delay(*args, **kwargs)
            logger.info(
                "Task '%s' triggered by user %s. Task ID: %s",
                task_name,
                request.user,
                result.id,
            )
            return Response(
                {"task_id": result.id, "status": "Task triggered successfully"},
                status=status.HTTP_200_OK,
            )
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "Failed to trigger task '%s'", task_name, exc_info=True
            )
            return Response(
                {"error": "Failed to trigger task"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
