from django.urls import path

from . import views

app_name = "htmx"
urlpatterns = [
    path("", views.SourceSystemListView.as_view(), name="sourcesystem-list"),
    path("create/", views.SourceSystemCreateView.as_view(), name="sourcesystem-create"),
    path("<int:pk>/update/", views.SourceSystemUpdateView.as_view(), name="sourcesystem-update"),
    path("<int:pk>/delete/", views.SourceSystemDeleteView.as_view(), name="sourcesystem-delete"),
    path("<int:pk>/token/", views.SourceSystemTokenView.as_view(), name="sourcesystem-token"),
    path("types/", views.SourceSystemTypeListView.as_view(), name="sourcesystemtype-list"),
    path("types/create/", views.SourceSystemTypeCreateView.as_view(), name="sourcesystemtype-create"),
    path("types/<str:pk>/delete/", views.SourceSystemTypeDeleteView.as_view(), name="sourcesystemtype-delete"),
]
