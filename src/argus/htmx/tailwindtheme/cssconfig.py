"""Shared rendering logic for Tailwind CSS config generation.

Pure functions with no Django dependencies. Used by both the Django management
command (tailwind_config) and the standalone build script (generate_css_config).
"""

import re

# Keys that are handled separately or have global side effects and should
# not be passed through to the generated CSS.
# - name: extracted from the dict key, written explicitly
# - default: makes a theme the page-wide default via :where(:root), which
#   overrides all user theme selections
# - prefersdark: generates a @media (prefers-color-scheme: dark) rule that
#   overrides all [data-theme] selections for dark-mode OS users
THEME_META_KEYS = frozenset({"name", "default", "prefersdark"})


def generate_theme_css(theme_name: str, theme_config: dict) -> str:
    """Generate CSS content for a DaisyUI v5 theme.

    Theme config keys are passed through directly as CSS properties.
    Keys starting with '--' are written as-is, other keys are written
    without the '--' prefix (for DaisyUI plugin options like color-scheme).
    """
    lines = [
        '@plugin "daisyui/theme" {',
        f'  name: "{theme_name}";',
    ]

    for key, value in theme_config.items():
        if key in THEME_META_KEYS:
            continue
        if key.startswith("--"):
            lines.append(f"  {key}: {value};")
        else:
            # Non-variable keys like color-scheme
            lines.append(f'  {key}: "{value}";')

    lines.append("}")
    lines.append("")  # trailing newline

    return "\n".join(lines)


def render_tailwind_css(template_text: str, builtin_themes: str) -> str:
    """Render tailwind.css template by substituting {{ builtin_themes }}."""
    placeholder = "{{ builtin_themes }}"
    if placeholder not in template_text:
        raise ValueError(f"Template is missing expected placeholder: {placeholder}")
    return template_text.replace(placeholder, builtin_themes)


def render_styles_css(template_text: str, css_files) -> str:
    """Render styles.css template by expanding the Django for-loop to @import lines."""
    import_lines = "".join(f"@import './{path}';\n" for path in css_files)

    pattern = r"\{% for cssfile in cssfiles %\}.*?\{% endfor %\}"
    if not re.search(pattern, template_text, flags=re.DOTALL):
        raise ValueError("Template is missing expected for-loop block: {% for cssfile in cssfiles %}")

    result = re.sub(
        pattern,
        import_lines,
        template_text,
        flags=re.DOTALL,
    )
    return result


def generate_config(themes, tailwind_template, styles_template, css_files, output_dir, log=print):
    """Generate all Tailwind CSS config files.

    This is the main orchestration function. Callers provide inputs
    (themes, template text, css files) gathered in their own way.
    """
    builtin_themes = ", ".join(t for t in themes if isinstance(t, str))

    # tailwind.css
    tailwind_css = render_tailwind_css(tailwind_template, builtin_themes)
    tailwind_path = output_dir / "tailwind.css"
    tailwind_path.write_text(tailwind_css)
    log(f"Wrote tailwind base config to '{tailwind_path}'")

    # Custom theme CSS files
    custom_themes_dir = output_dir / "custom-themes"
    custom_themes_dir.mkdir(exist_ok=True)
    for theme in themes:
        if isinstance(theme, dict):
            for theme_name, theme_config in theme.items():
                path = custom_themes_dir / f"{theme_name}.css"
                path.write_text(generate_theme_css(theme_name, theme_config))
                log(f"Wrote theme '{theme_name}' to '{path}'")

    # styles.css
    styles_css = render_styles_css(styles_template, css_files)
    styles_path = output_dir / "styles.css"
    styles_path.write_text(styles_css)
    log(f"Wrote tailwind base css to '{styles_path}'")
