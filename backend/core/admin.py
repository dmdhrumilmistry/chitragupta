from django.contrib import admin

from .models import Repo, RepoOwner

admin.site.register(Repo)
admin.site.register(RepoOwner)