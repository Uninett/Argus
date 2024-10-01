from django.db import models

# Prevent import loops
# DO NOT import anything from argus here, ever


class Level(models.IntegerChoices):
    CRITICAL = 1, "Critical"
    HIGH = 2, "High"
    MODERATE = 3, "Moderate"
    LOW = 4, "Low"
    INFORMATION = 5, "Information"


INCIDENT_LEVELS = tuple(Level.values)
INCIDENT_LEVEL_CHOICES = tuple(zip(INCIDENT_LEVELS, map(str, INCIDENT_LEVELS)))
