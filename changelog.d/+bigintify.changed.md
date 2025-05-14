The primary keys of the models Incident, Tag, IncidentTagRelation and Event
(and indirectly Acknowledgment) were changed from a 32-bit signed integer to
a 64-bit signed integer since these may grow for all eternity.
