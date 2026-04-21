from datetime import timedelta

from django.http.request import QueryDict
from django.test import TestCase
from django.utils import timezone

from argus.incident.models import Incident
from argus.incident.factories import IncidentFactory
from argus.htmx.incident.forms.incident_filters import DescriptionForm, HasTicketForm, IdForm, IsUnderMaintenanceForm
from argus.plannedmaintenance.factories import PlannedMaintenanceFactory


class IdFormTest(TestCase):
    class obj:
        pass

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.incident = IncidentFactory(id=95)
        IncidentFactory()

    def test_form_without_input_returns_every_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="")
        form = IdForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(qs, result_qs)

    def test_form_with_unfound_input_returns_empty_queryset(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="id=14063")
        form = IdForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertFalse(result_qs.exists())

    def test_form_with_irrelevant_input_returns_every_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="otherkey=1234")
        form = IdForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(qs, result_qs)

    def test_form_with_found_input_returns_specific_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="id=95")
        form = IdForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(result_qs.count(), 1)
        self.assertEqual(result_qs[0], self.incident)


class DescriptionFormTest(TestCase):
    class obj:
        pass

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.incident = IncidentFactory(description="jubalong")
        IncidentFactory()

    def test_form_without_input_returns_every_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="")
        form = DescriptionForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(qs, result_qs)

    def test_form_with_unfound_input_returns_empty_queryset(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="description=1234")
        form = DescriptionForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertFalse(result_qs.exists())

    def test_form_with_irrelevant_input_returns_every_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="otherkey=1234")
        form = DescriptionForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(qs, result_qs)

    def test_form_with_found_input_returns_specific_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="description=balo")
        form = DescriptionForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(result_qs.count(), 1)
        self.assertEqual(result_qs[0], self.incident)


class HasTicketFormTest(TestCase):
    class obj:
        pass

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.incident1 = IncidentFactory(ticket_url="http://example.org/56757/")
        cls.incident2 = IncidentFactory(ticket_url="")

    def test_form_without_input_returns_every_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="")
        form = HasTicketForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(qs, result_qs)

    def test_form_with_unfound_input_returns_every_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="has_ticket=blbl")
        form = HasTicketForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(qs, result_qs)

    def test_form_with_irrelevant_input_returns_every_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="otherkey=1234")
        form = HasTicketForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(qs, result_qs)

    def test_form_with_input_yes_returns_specific_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="has_ticket=yes")
        form = HasTicketForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(result_qs.count(), 1)
        self.assertEqual(result_qs[0], self.incident1)

    def test_form_with_input_no_returns_specific_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="has_ticket=no")
        form = HasTicketForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(result_qs.count(), 1)
        self.assertEqual(result_qs[0], self.incident2)


class IsUnderMaintenanceFormTest(TestCase):
    class obj:
        pass

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        now = timezone.now()
        cls.under_maintenance_incident = IncidentFactory()
        cls.not_under_maintenance_incident = IncidentFactory()

        cls.maintenance = PlannedMaintenanceFactory(
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
        )

        cls.maintenance.incidents.add(cls.under_maintenance_incident)

    def test_form_without_input_returns_every_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="")
        form = IsUnderMaintenanceForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(qs, result_qs)

    def test_form_with_unfound_input_returns_every_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="is_under_maintenance=blbl")
        form = IsUnderMaintenanceForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(qs, result_qs)

    def test_form_with_irrelevant_input_returns_every_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="otherkey=1234")
        form = IsUnderMaintenanceForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertEqual(qs, result_qs)

    def test_form_with_input_yes_returns_specific_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="is_under_maintenance=yes")
        form = IsUnderMaintenanceForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertIn(self.under_maintenance_incident, result_qs)
        self.assertNotIn(self.not_under_maintenance_incident, result_qs)

    def test_form_with_input_no_returns_specific_incident(self):
        qs = Incident.objects.all()
        request = self.obj()

        request.GET = QueryDict(query_string="is_under_maintenance=no")
        form = IsUnderMaintenanceForm(data=request.GET)
        result_qs = form.filter(qs, request)
        self.assertIn(self.not_under_maintenance_incident, result_qs)
        self.assertNotIn(self.under_maintenance_incident, result_qs)
