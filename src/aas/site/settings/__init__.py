from pathlib import Path


__all__ = [
    'SETTINGS_DIR',
    'SITE_DIR',
    'BASE_DIR',
]

# Build paths inside the project like this: BASE_DIR / ...
SETTINGS_DIR = Path(__file__).resolve().parent
SITE_DIR = SETTINGS_DIR.parent
BASE_DIR = SITE_DIR.parent
