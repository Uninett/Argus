#! /usr/bin/env python3

# Do not import anything not included with python here
# Allows it to work without an activated virtualenv


from argus.htmx.tailwindtheme.config import FILENAME, VERSION
from argus.htmx.tailwindtheme.utils import (
    get_url,
    get_architecture,
    map_from_architecture_to_filename_fragment,
    download_tailwind_cli,
)


if __name__ == "__main__":
    architecture = get_architecture()
    print(f"About to download tailwind version {VERSION} for {architecture}")

    fragment = map_from_architecture_to_filename_fragment(*architecture)

    url = get_url(VERSION, fragment)
    print(f"- Fetch from {url}")

    print(f"- Store in {FILENAME}")

    download_tailwind_cli(url, FILENAME)
    print(f"Successfully downloaded tailwind version {VERSION} for {architecture} to {FILENAME}")
