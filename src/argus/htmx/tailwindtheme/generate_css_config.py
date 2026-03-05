#! /usr/bin/env python3

"""Generate Tailwind CSS config files without Django.

Standalone build-time alternative to the `tailwind_config` management command.
Only uses stdlib + local modules (no Django dependencies).

This generates the config needed for a default Argus build. Custom themes can
be provided via the DAISYUI_THEMES environment variable (JSON list), e.g.:

    DAISYUI_THEMES='["dark","light",{"custom":{"--color-primary":"#f00"}}]'

For third-party app CSS discovery, use the Django management command instead.
"""

import json
import os
from pathlib import Path

from argus.htmx.tailwindtheme.config import DEFAULT_THEMES
from argus.htmx.tailwindtheme.cssconfig import generate_config


TAILWINDTHEME_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = TAILWINDTHEME_DIR.parent / "templates" / "tailwind"


def get_themes():
    """Read themes from DAISYUI_THEMES env var, falling back to DEFAULT_THEMES."""
    env_value = os.environ.get("DAISYUI_THEMES")
    if env_value is not None:
        return json.loads(env_value)
    return DEFAULT_THEMES


def get_css_files():
    """Discover CSS files the same way HtmxFrontendConfig.tailwind_css_files does."""
    for pattern in ("snippets/*.css", "themes/*.css", "custom-themes/*.css"):
        yield from sorted(TAILWINDTHEME_DIR.glob(pattern), key=lambda p: p.stem)


def main():
    themes = get_themes()
    tailwind_template = (TEMPLATE_DIR / "tailwind.css").read_text()
    styles_template = (TEMPLATE_DIR / "styles.css").read_text()
    css_files = (p.relative_to(TAILWINDTHEME_DIR) for p in get_css_files())

    generate_config(themes, tailwind_template, styles_template, css_files, TAILWINDTHEME_DIR)


if __name__ == "__main__":
    main()
