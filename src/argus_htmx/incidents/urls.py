from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("", views.incident_list, name="incident-list"),
    path("<int:pk>/", views.incident_detail, name="incident-detail"),
    path("<int:pk>/ack/", views.incident_add_ack, name="incident-add-ack"),
    path("<int:pk>/ack-detail/", views.incident_detail_add_ack, name="incident-detail-add-ack"),
    path("<int:pk>/close-detail/", views.incident_detail_close, name="incident-detail-close"),
    path("<int:pk>/reopen-detail/", views.incident_detail_reopen, name="incident-detail-reopen"),
    path("<int:pk>/ticket-edit-detail/", views.incident_detail_edit_ticket, name="incident-detail-edit-ticket"),
    path("<int:pk>/ticket-add-detail/", views.incident_detail_add_ticket, name="incident-detail-add-ticket"),
    path("update/<str:action>/", views.incidents_update, name="incidents-update"),
]
