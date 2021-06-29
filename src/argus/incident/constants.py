# Prevent import loops
# DO NOT import anything here, ever

MIN_INCIDENT_LEVEL = 1  # Do not override
MAX_INCIDENT_LEVEL = 5
INCIDENT_LEVELS = tuple(range(MIN_INCIDENT_LEVEL, MAX_INCIDENT_LEVEL + 1))
INCIDENT_LEVEL_CHOICES = zip(INCIDENT_LEVELS, map(str, INCIDENT_LEVELS))
