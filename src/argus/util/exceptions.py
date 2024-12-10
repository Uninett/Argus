class SuccessfulRepairException(Exception):
    # Something was repaired and we need to skip another action
    pass


class InconceivableException(Exception):
    # This should not happen, ever!
    pass


class InconsistentDatabaseException(ValueError):
    # Something is missing or doubled up in the database, or has neen accidentally deleted
    pass
