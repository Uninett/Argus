from django.urls import path

from . import views

app_name = "alert"
urlpatterns = [
    path("", views.AlertList.as_view()),
    # path("create/", login_required(views.CreateAlertView.as_view()), name="create"),
    path("source/<int:source_pk>", views.all_alerts_from_source_view, name="source"),
    path("problem_types", views.get_problem_types_view)
]
