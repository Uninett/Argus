from unittest.mock import Mock, patch

from django.test import TestCase

from argus.notificationprofile.tasks import task_check_for_notifications, task_send_notifications


class TestTaskSendNotifications(TestCase):
    def test_unknown_event_aborts_early(self):
        with patch("argus.notificationprofile.tasks.DestinationConfig.objects.get") as get_destination:
            task_send_notifications.func(0, 0)
            get_destination.assert_not_called()

    @patch("argus.notificationprofile.tasks.Event.objects")
    def test_known_event_but_unknown_destination_aborts_early(self, event_qs):
        event_qs.get.return_value = "foo"
        with patch("argus.notificationprofile.tasks.send_notification") as send:
            task_send_notifications.func(0, 0)
            send.assert_not_called()

    @patch("argus.notificationprofile.tasks.Event.objects")
    def test_known_event_and_destination_calls_send_notification(self, event_qs):
        event_qs.get.return_value = Mock()
        with patch("argus.notificationprofile.tasks.DestinationConfig.objects") as destination_qs:
            destination_qs.get.return_value = Mock()
            with patch("argus.notificationprofile.tasks.send_notification") as send:
                task_send_notifications.func(0, 0)
                send.assert_called()


class TestTaskCheckForNotifications(TestCase):
    def test_unknown_event_aborts_early(self):
        with patch("argus.notificationprofile.tasks.find_destinations_for_event") as guard:
            task_check_for_notifications.func(0)
            guard.assert_not_called()

    @patch("argus.notificationprofile.tasks.Event.objects")
    def test_known_event_but_no_destinations_aborts_early(self, event_qs):
        event_qs.get.return_value = "foo"
        with patch("argus.notificationprofile.tasks.find_destinations_for_event", return_value=False) as guard:
            task_check_for_notifications.func(0)
            guard.assert_called_once()

    @patch("argus.notificationprofile.tasks.Event.objects")
    def test_known_event_and_destinations_calls_task_send_notifications(self, event_qs):
        event_qs.get.return_value = "foo"
        destination1 = Mock()
        destination1.id = 1
        destination2 = Mock()
        destination2.id = 2
        with patch(
            "argus.notificationprofile.tasks.find_destinations_for_event",
            return_value=(destination1, destination2),
        ) as guard:
            with patch("argus.notificationprofile.tasks.task_send_notifications") as task:
                task.enqueue.return_value = None
                task_check_for_notifications.func(0)
                guard.assert_called_once()
                self.assertEqual(task.enqueue.call_count, 2)
