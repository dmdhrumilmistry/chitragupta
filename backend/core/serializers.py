from rest_framework.serializers import ModelSerializer
from .models import Repo, RepoOwner


class RepoOwnerSerializer(ModelSerializer):
    class Meta:
        model = RepoOwner
        exclude = ['created_at', 'updated_at', 'id']


class RepoSerializer(ModelSerializer):
    class Meta:
        model = Repo
        exclude = ['created_at', 'updated_at', 'id']