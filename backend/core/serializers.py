from rest_framework.serializers import ModelSerializer, SerializerMethodField
from .models import Repo, RepoOwner, SecretScanResult


class RepoOwnerSerializer(ModelSerializer):
    id = SerializerMethodField(read_only=True)

    class Meta:
        model = RepoOwner
        exclude = ["created_at", "updated_at"]

    def get_id(self, obj):
        return str(obj.id)


class RepoSerializer(ModelSerializer):
    id = SerializerMethodField(read_only=True)
    owner = RepoOwnerSerializer(read_only=True)

    class Meta:
        model = Repo
        exclude = ["created_at", "updated_at"]

    def get_id(self, obj):
        return str(obj.id)


class SecretScanResultSerializer(ModelSerializer):
    id = SerializerMethodField(read_only=True)
    repo = RepoSerializer(read_only=True)

    class Meta:
        model = SecretScanResult
        exclude = ["created_at", "updated_at"]

    def get_id(self, obj):
        return str(obj.id)
