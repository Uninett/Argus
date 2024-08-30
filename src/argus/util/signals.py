import django.dispatch

__all__ = ["bulk_changed"]


bulk_changed = django.dispatch.Signal()
