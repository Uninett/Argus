MAX_LEVEL = 5
IGNORABLE = {
    "open": None,
    "acked": None,
    "stateful": None,
    "sourceSystemIds": [],
    "source_types": [],
    "tags": [],
    "event_types": [],
    "maxlevel": MAX_LEVEL,
}


def minimalize_filterblob(filterblob):
    """Strip away lookups to be ignored"""
    minimal_filterblob = filterblob.copy()
    for key, value in filterblob.items():
        if key in IGNORABLE and value == IGNORABLE[key]:
            del minimal_filterblob[key]

    return minimal_filterblob
