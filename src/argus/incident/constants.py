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
    UNACKED = 2, "Unacked"
    BOTH = 3, "Both"


class OpenStatus(models.IntegerChoices):
    OPEN = 1, "Open"
    CLOSED = 2, "Closed"
    BOTH = 3, "Both"
