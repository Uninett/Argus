# customize the displayed columns in the incident table
# items in INCIDENT_TABLE_COLUMNS can be either a `str` referring to a key in
# argus_htmx.incidents.customization.BUILTIN_COLUMNS or an instance of
# argus_htmx.incidents.customization.IncidentTableColumn
from argus.site.settings import get_json_env

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

# Tailwind config template relative to the repository root directory
TAILWIND_CONFIG_TEMPLATE = "src/argus_htmx/tailwindtheme/tailwind.config.template.js"
TAILWIND_CONFIG_TARGET = "src/argus_htmx/tailwindtheme/tailwind.config.js"

DEFAULT_THEMES = ["dark", "light", {
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
        "error-content": "#120203"
    }
}]
DAISYUI_THEMES = get_json_env("DAISYUI_THEMES", DEFAULT_THEMES, quiet=True)
DEFAULT_THEME_OVERRIDE = {}
TAILWIND_THEME_OVERRIDE = get_json_env("TAILWIND_THEME_OVERRIDE", DEFAULT_THEME_OVERRIDE, quiet=True)
