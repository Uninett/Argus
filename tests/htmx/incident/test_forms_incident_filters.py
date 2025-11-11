from django.http.request import QueryDict
from django.test import TestCase

from argus.incident.models import Incident
from argus.incident.factories import IncidentFactory
from argus.htmx.incident.forms.incident_filters import DescriptionForm, HasTicketForm


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
