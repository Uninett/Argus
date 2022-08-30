from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.test import TestCase

from argus.incident.factories import StatefulIncidentFactory
from argus.incident.issue import _import_class_from_dotted_path
from argus.util.testing import disconnect_signals, connect_signals


class IssueUrlTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(IssueUrlTestCase, cls).setUpClass()
        disconnect_signals()
        cls.incident = StatefulIncidentFactory()

    @classmethod
    def tearDownClass(cls):
        super(IssueUrlTestCase, cls).tearDownClass()
        connect_signals()

    def test_gitlab_plugin_generates_valid_url(self):
        try:
            gitlab_class = _import_class_from_dotted_path("argus.incident.issue.gitlab.GitlabPlugin")
        except:
            self.skipTest()
        issue_url = gitlab_class.generate_issue_url(self.incident)
        validator = URLValidator()
        try:
            validator(issue_url)
        except ValidationError:
            self.fail(msg=f"Generated url '{issue_url}' is not a valid url.")

    def test_request_tracker_plugin_generates_valid_url(self):
        try:
            request_tracker_class = _import_class_from_dotted_path("argus.incident.issue.gitlab.GitlabPlugin")
        except:
            self.skipTest()
        issue_url = request_tracker_class.generate_issue_url(self.incident)
        validator = URLValidator()
        try:
            validator(issue_url)
        except ValidationError:
            self.fail(msg=f"Generated url '{issue_url}' is not a valid url.")
