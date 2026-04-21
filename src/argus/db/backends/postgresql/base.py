import functools
from datetime import timezone

from django.db.backends.postgresql.base import DatabaseWrapper as DjangoDatabaseWrapper
from psycopg.abc import Loader
from psycopg.postgres import types
from psycopg.pq import Format

from argus.util.datetime_utils import INFINITY, NEGATIVE_INFINITY


# PostgreSQL type OIDs used to register custom loaders
TIMESTAMPTZ_OID = types["timestamptz"].oid
TIMESTAMP_OID = types["timestamp"].oid

# Wire-format representations of PostgreSQL infinity timestamps
INFINITY_TEXT = b"infinity"
NEGATIVE_INFINITY_TEXT = b"-infinity"
# Binary: signed int64 microsecond offset from the PG epoch (2000-01-01)
# https://github.com/psycopg/psycopg/blob/3.3.3/psycopg/psycopg/types/datetime.py#L266-L269
INFINITY_BINARY = b"\x7f\xff\xff\xff\xff\xff\xff\xff"
NEGATIVE_INFINITY_BINARY = b"\x80\x00\x00\x00\x00\x00\x00\x00"

# UTC-aware sentinels for the loaders (must match the naive values in datetime_utils)
INFINITY_UTC = INFINITY.replace(tzinfo=timezone.utc)
NEGATIVE_INFINITY_UTC = NEGATIVE_INFINITY.replace(tzinfo=timezone.utc)


class DatabaseWrapper(DjangoDatabaseWrapper):
    def get_new_connection(self, conn_params):
        conn = super().get_new_connection(conn_params)

        _register_inf_loaders(conn.adapters, TIMESTAMPTZ_OID, Format.TEXT, Format.BINARY)
        _register_inf_loaders(conn.adapters, TIMESTAMP_OID, Format.TEXT, Format.BINARY)

        return conn


def _register_inf_loaders(adapters, oid, text_format, binary_format):
    """Register infinity-aware loaders that subclass the already-registered ones."""
    current_text_cls = adapters.get_loader(oid, text_format)
    current_binary_cls = adapters.get_loader(oid, binary_format)
    adapters.register_loader(oid, _make_inf_loader(current_text_cls, INFINITY_TEXT, NEGATIVE_INFINITY_TEXT))
    adapters.register_loader(oid, _make_inf_loader(current_binary_cls, INFINITY_BINARY, NEGATIVE_INFINITY_BINARY))


@functools.lru_cache(maxsize=8)
def _make_inf_loader(parent_class, inf_text, neg_inf_text):
    """Create an infinity-aware loader.

    Tries subclassing first (works for pure-Python loaders and preserves
    Django's timezone attribute). Falls back to a wrapper for C-extension
    loaders that cannot be subclassed.

    Results are cached so loader classes are created once, not per-connection.
    """
    try:

        class InfLoader(parent_class):
            def load(self, data):
                if data == inf_text:
                    return INFINITY_UTC
                if data == neg_inf_text:
                    return NEGATIVE_INFINITY_UTC
                return super().load(data)

        # Access .format to verify the subclass inherited it correctly
        InfLoader.format  # noqa: B018
        return InfLoader

    except TypeError:
        # C-extension loaders (psycopg-c/psycopg-binary) cannot be subclassed.
        # Use a wrapper that delegates to an instance of the original.
        class InfLoaderWrapper(Loader):
            format = parent_class.format

            def __init__(self, oid, context=None):
                super().__init__(oid, context)
                self._delegate = parent_class(oid, context)

            def load(self, data):
                if data == inf_text:
                    return INFINITY_UTC
                if data == neg_inf_text:
                    return NEGATIVE_INFINITY_UTC
                return self._delegate.load(data)

        # Copy the timezone attribute that Django inspects on the loader
        # to determine cursor timezone (see Django's create_cursor).
        if hasattr(parent_class, "timezone"):
            InfLoaderWrapper.timezone = parent_class.timezone

        return InfLoaderWrapper
