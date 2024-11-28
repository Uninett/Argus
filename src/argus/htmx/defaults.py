# customize the displayed columns in the incident table
# items in INCIDENT_TABLE_COLUMNS can be either a `str` referring to a key in
# argus.htmx.incidents.customization.BUILTIN_COLUMNS or an instance of
# argus.htmx.incidents.customization.IncidentTableColumn
from argus.site.settings import get_json_env, get_str_env

INCIDENT_TABLE_COLUMNS = [
    "row_select",
    "id",
    "start_time",
    "combined_status",
    "level",
    "source",
    "description",
    "ticket",
]

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
    {
        "argus": {
            "primary": "#006d91",
            "primary-content": "#d1e1e9",
            "secondary": "#f3b61f",
            "secondary-content": "#140c00",
            "accent": "#c84700",
            "accent-content": "#f8dbd1",
            "neutral": "#006d91",
            "neutral-content": "#d1e1e9",
            "base-100": "#edfaff",
            "base-200": "#ced9de",
            "base-300": "#b0babd",
            "base-content": "#141516",
            "info": "#0073e5",
            "info-content": "#000512",
            "success": "#008700",
            "success-content": "#d3e7d1",
            "warning": "#ee4900",
            "warning-content": "#140200",
            "error": "#e5545a",
            "error-content": "#120203",
        }
    },
]
DAISYUI_THEMES = get_json_env("DAISYUI_THEMES", DEFAULT_THEMES, quiet=True)
THEME_DEFAULT = get_str_env("ARGUS_THEME_DEFAULT", "argus")
DEFAULT_THEME_OVERRIDE = {}
TAILWIND_THEME_OVERRIDE = get_json_env("TAILWIND_THEME_OVERRIDE", DEFAULT_THEME_OVERRIDE, quiet=True)
STYLESHEET_PATH = get_str_env("ARGUS_STYLESHEET_PATH", STYLESHEET_PATH_DEFAULT)
