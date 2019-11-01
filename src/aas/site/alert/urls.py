from django.urls import path

from . import views

app_name = "alert"
urlpatterns = [
    path("", views.AlertList.as_view()),
    path("<int:pk>", views.AlertDetail.as_view()),
    # path("create/", login_required(views.CreateAlertView.as_view()), name="create"),

    path("source/<int:source_pk>", views.all_alerts_from_source_view, name="source"),

    path("metaData", views.get_all_meta_data_view),


]
