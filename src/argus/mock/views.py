from django.shortcuts import render, get_object_or_404

from faker import Faker

from argus.incident.models import Incident


def mock_detail(request, pk: int):
    incident = get_object_or_404(Incident, pk=pk)
    source_id = incident.source_incident_id

    fake = Faker()
    Faker.seed(source_id)

    context = {
        "pk": pk,
        "lorem": fake.paragraphs(),
    }
    return render(request, "mock/detail.html", context=context)
