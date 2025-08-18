# customize the displayed columns in the incident table
# items in INCIDENT_TABLE_COLUMNS can be either a `str` referring to a key in
# argus.htmx.incident.columns.BUILTIN_COLUMNS or an instance of
# argus.htmx.incident.columns.IncidentTableColumn
from argus.site.settings import get_json_env, get_str_env


HTMX_PATH_DEFAULT = "htmx-2.0.2.min.js"
HYPERSCRIPT_PATH_DEFAULT = "hyperscript-0.9.13.min.js"
INCIDENT_TABLE_COLUMNS = [
    "color_status",
    "row_select",
    "start_time",
    "combined_status",
    "level",
    "source",
    "description",
    "ticket",
]
DEFAULT_INCIDENT_TABLE_COLUMN_LAYOUTS = {
    "built-in": INCIDENT_TABLE_COLUMNS,
    "notifications": [
        "status_icon",
        "ack_icon",
        "level",
        "source_type",
        "source",
        "tags",
        "events",
    ],
    "on maintenance": [
        "source_type",
        "source",
        "tags",
    ],
}
ARGUS_HTMX_FILTER_FUNCTION = "argus.htmx.incident.filter.incident_list_filter"

# These templates are auto-discovered by the templating engine and are relative
# to the argus.htmx's `templates/` directory
TAILWIND_CONFIG_TEMPLATE = "tailwind/tailwind.config.js"
TAILWIND_CSS_TEMPLATE = "tailwind/styles.css"

# These targets are relative to the working directory when running the `tailwind_config`
# management command, which should be done from the repostitory root
TAILWIND_CONFIG_TARGET = "src/argus/htmx/tailwindtheme/tailwind.config.js"
TAILWIND_CSS_TARGET = "src/argus/htmx/tailwindtheme/styles.css"

STYLESHEET_PATH_DEFAULT = "styles.css"
DEFAULT_THEMES = [
    "dark",
    "light",
    "argus",
]
DAISYUI_THEMES = get_json_env("DAISYUI_THEMES", DEFAULT_THEMES, quiet=True)
THEME_DEFAULT = get_str_env("ARGUS_THEME_DEFAULT", "argus")
DEFAULT_THEME_OVERRIDE = {}
TAILWIND_THEME_OVERRIDE = get_json_env("TAILWIND_THEME_OVERRIDE", DEFAULT_THEME_OVERRIDE, quiet=True)

STYLESHEET_PATH = get_str_env("ARGUS_STYLESHEET_PATH", STYLESHEET_PATH_DEFAULT)
HTMX_PATH = get_str_env("ARGUS_HTMX_PATH", HTMX_PATH_DEFAULT)
HYPERSCRIPT_PATH = get_str_env("ARGUS_HYPERSCRIPT_PATH", HYPERSCRIPT_PATH_DEFAULT)
CHOICES_PATH = "choices-11.1.0.min.js"

NOTIFICATION_TOAST_AUTOCLOSE_SECONDS = {
    "success": 10,
    "autoclose": 10,
}
