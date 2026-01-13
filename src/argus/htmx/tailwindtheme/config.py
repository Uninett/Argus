from pathlib import Path


VERSION = "2.1.37"

TAILWIND_EXTRA_URL = (
    "https://github.com/dobicinaitis/tailwind-cli-extra/releases/download/v{version}/tailwindcss-extra-{arch}"
)

# This might need to be updated when the version is updated!
ARCHITECTURE_MAP = {
    ("linux", "x86_64"): "linux-x64",
    ("linux", "x86_64-musl"): "linux-x64-musl",
    ("linux", "arm64"): "linux-arm64",
    ("linux", "arm64-musl"): "linux-arm64-musl",
    ("darwin", "x86_64"): "macos-x64",
    ("darwin", "arm"): "macos-arm64",
    ("darwin", "arm64"): "macos-arm64",
    ("windows", "x86_64"): "windows-x64",
}

# Probably no need to ever change these

TAILWIND_PATH = Path(__file__).resolve()

FILENAME = TAILWIND_PATH.parent / "tailwindcss"

__all__ = [
    "VERSION",
    "ARCHITECTURE_MAP",
    "TAILWIND_PATH",
    "TAILWIND_EXTRA_URL",
    "FILENAME",
]
