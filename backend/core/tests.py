"""
Core tests for Chitragupta API.
"""

from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status


class TriggerTaskViewTests(TestCase):
    """
    Test cases for TriggerTaskView.
    """

    def setUp(self):
        self.client = APIClient()
        self.superuser = User.objects.create_superuser(
            username="admin", password="password", email="admin@example.com"
        )
        self.user = User.objects.create_user(
            username="user", password="password", email="user@example.com"
        )
        self.url = "/api/core/trigger-task/"  # Adjust based on urls.py inclusion

    def test_trigger_task_unauthenticated(self):
        """
        Test that unauthenticated users cannot trigger tasks.
        """
        response = self.client.post(self.url, {"task_name": "scan_repo"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_trigger_task_non_admin(self):
        """
        Test that non-admin users cannot trigger tasks.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"task_name": "scan_repo"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("core.views.scan_repo.delay")
    def test_trigger_task_success(self, mock_delay):
        """
        Test that admin users can trigger tasks successfully.
        """
        mock_delay.return_value.id = "12345"
        self.client.force_authenticate(user=self.superuser)

        payload = {
            "task_name": "scan_repo",
            "kwargs": {"repo_pk": "1"}
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["task_id"], "12345")
        mock_delay.assert_called_once_with(repo_pk="1")

    def test_trigger_invalid_task(self):
        """
        Test that invalid tasks are rejected.
        """
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(self.url, {"task_name": "invalid_task"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
