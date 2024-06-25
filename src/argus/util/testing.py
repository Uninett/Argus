# import the signal sender (aka. post_save)

# import the signal receivers

__all__ = [
    "disconnect_signals",
    "connect_signals",
]


# Signals that close the database connection, interferes with some tests


def disconnect_signals():
    # signal.disconnect(receiver)
    pass


def connect_signals():
    # signal.connect(receiver)
    pass
