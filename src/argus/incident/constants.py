# Prevent import loops
# DO NOT import anything here, ever

INCIDENT_LEVELS = (1, 2, 3, 4, 5)
INCIDENT_LEVEL_CHOICES = zip(INCIDENT_LEVELS, map(str, INCIDENT_LEVELS))
