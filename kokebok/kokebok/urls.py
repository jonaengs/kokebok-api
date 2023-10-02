from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("controls/", admin.site.urls),
    path("api/", include("recipes.api")),
]
