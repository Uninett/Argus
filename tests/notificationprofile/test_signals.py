from unittest.mock import Mock, patch

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, tag

from argus.notificationprofile.media.base import AppriseMedium
from argus.notificationprofile.media.email import EmailNotification
from argus.notificationprofile.media.slack import SlackNotification
from argus.notificationprofile.signals import sync_media, task_background_send_notification


@tag("integration", "signal")
class SyncMediaAppriseAvailabilityTests(TestCase):
    @patch("argus.notificationprofile.media.base.Apprise", object())
    def test_when_apprise_is_available_should_not_raise(self):
        sync_media(None, apps=apps)

    @patch("argus.notificationprofile.media.base.Apprise", None)
    @patch("argus.notificationprofile.media.MEDIA_CLASSES_DICT", {"email": EmailNotification})
    def test_when_apprise_is_missing_and_no_apprise_derived_medium_is_configured_should_not_raise(self):
        sync_media(None, apps=apps)

    @patch("argus.notificationprofile.media.base.Apprise", None)
    @patch(
        "argus.notificationprofile.media.MEDIA_CLASSES_DICT",
        {"slack": SlackNotification, "apprise": AppriseMedium, "email": EmailNotification},
    )
    def test_when_apprise_is_missing_should_raise_with_only_apprise_derived_medium(self):
        with self.assertRaises(ImproperlyConfigured) as cm:
            sync_media(None)

        self.assertIn("SlackNotification", str(cm.exception))
        self.assertIn("AppriseMedium, SlackNotification", str(cm.exception))
        self.assertNotIn("EmailNotification", str(cm.exception))


@tag("unit", "signal")
class TestTaskBackgroundSendNotification(SimpleTestCase):
    def test_if_covered_by_planned_maintenance_abort_early(self):
        with patch(
            "argus.notificationprofile.signals.event_covered_by_planned_maintenance", return_value=True
        ) as guard:
            with patch("argus.notificationprofile.signals.task_check_for_notifications") as task:
                task.enqueue.return_value = "blapp"
                task_background_send_notification(None, None)
                guard.assert_called_once_with(event=None)
                task.enqueue.assert_not_called()

    def test_if_not_covered_by_planned_maintenance_enquque_task(self):
        with patch(
            "argus.notificationprofile.signals.event_covered_by_planned_maintenance", return_value=False
        ) as guard:
            with patch("argus.notificationprofile.signals.task_check_for_notifications") as task:
                event = Mock()
                event.id = "blapp"
                task.enqueue.return_value = "goo"
                task_background_send_notification(None, event)
                guard.assert_called_once_with(event=event)
                task.enqueue.assert_called_once_with("blapp")
