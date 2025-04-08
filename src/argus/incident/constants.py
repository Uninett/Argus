from django.db import models

# Prevent import loops
# DO NOT import anything from argus here, ever


class Level(models.IntegerChoices):
    CRITICAL = 1, "Critical"
    HIGH = 2, "High"
    MODERATE = 3, "Moderate"
    LOW = 4, "Low"
    INFORMATION = 5, "Information"


class AckedStatus(models.IntegerChoices):
    ACKED = 1, "Acked"
    BOTH = 2, "Both"
    UNACKED = 3, "Unacked"


class OpenStatus(models.IntegerChoices):
    OPEN = 1, "Open"
    BOTH = 2, "Both"
    CLOSED = 3, "Closed"
