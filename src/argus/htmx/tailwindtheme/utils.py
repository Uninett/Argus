# Do not import anything not included with python here
# Allows it to work without an activated virtualenv

import platform
from urllib import request

from .config import ARCHITECTURE_MAP, TAILWIND_EXTRA_URL


__all__ = [
    "get_url",
    "get_architecture",
    "map_from_architecture_to_filename_fragment",
    "download_tailwind_cli",
]


def get_url(version, architecture):
    base_url = TAILWIND_EXTRA_URL.format(version=version, arch=architecture)
    return base_url


def get_architecture():
    uname_obj = platform.uname()
    processor = uname_obj.processor.lower() or uname_obj.machine.lower()
    libc, _ = platform.libc_ver()
    if libc == "musl":
        processor += f"-{libc}"
    system = uname_obj.system.lower()
    return (system, processor)


def map_from_architecture_to_filename_fragment(system, processor):
    try:
        fragment = ARCHITECTURE_MAP[(system, processor)]
    except KeyError:
        raise Exception(f'Unsupported platform "{system}", "{processor}"')
    if system == "windows":
        fragment += ".exe"
    return fragment


def download_tailwind_cli(url, filename):
    request.urlretrieve(url, str(filename))
    filename.chmod(0o755)
