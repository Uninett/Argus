# Gunicorn configuration file
# https://gunicorn.org/configure/#configuration-file
# https://gunicorn.org/reference/settings/

# logging

accesslog = "-"
errorlog = "-"

access_log_format = '"%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
loglevel = "info"  # gunicorn error log, hide noise
