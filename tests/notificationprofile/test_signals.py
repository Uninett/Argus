from unittest.mock import Mock, patch

from django.test import SimpleTestCase, tag

from argus.notificationprofile.signals import task_background_send_notification


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
