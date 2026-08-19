import logging


LOG = logging.getLogger(__name__)


class HeartBeatMixin:
    def initial(self, request, *args, **kwargs):
        # ensure we are logged in
        super().initial(request, *args, **kwargs)

        if request.user.is_authenticated and request.user.is_source_system:
            LOG.info("Heartbeat: %s", request.user.source_system.name)
            request.user.source_system.update_last_seen()
