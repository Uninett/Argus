from zoneinfo import ZoneInfo

import factory

from argus.auth.factories import PersonUserFactory
from argus.plannedmaintenance import models
from argus.util.datetime_utils import LOCAL_INFINITY


__all__ = [
    "PlannedMaintenanceFactory",
]


class PlannedMaintenanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PlannedMaintenanceTask

    created_by = factory.SubFactory(PersonUserFactory)
    start_time = factory.Faker("date_time_between", start_date="-2d", end_date="-1d", tzinfo=ZoneInfo("UTC"))
    end_time = LOCAL_INFINITY
    description = factory.Faker("sentence")
