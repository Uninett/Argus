from django.db import models

# Prevent import loops
# DO NOT import anything here, ever

MIN_INCIDENT_LEVEL = 1  # Do not override
MAX_INCIDENT_LEVEL = 5
INCIDENT_LEVELS = tuple(range(MIN_INCIDENT_LEVEL, MAX_INCIDENT_LEVEL + 1))
INCIDENT_LEVEL_CHOICES = tuple(zip(INCIDENT_LEVELS, map(str, INCIDENT_LEVELS)))


class Level(models.IntegerChoices):
    CRITICAL = 1, "Critical"
    HIGH = 2, "High"
    MODERATE = 3, "Moderate"
    LOW = 4, "Low"
    INFORMATION = 5, "Information"
