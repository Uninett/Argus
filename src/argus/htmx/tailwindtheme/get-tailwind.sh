#! /usr/bin/env bash

set -eu -o pipefail

SCRIPT_PATH="$(dirname "${BASH_SOURCE[0]}")"
cd "$SCRIPT_PATH"

TAILWIND_EXTRA_VERSION="$(head VERSION)"
TAILWIND_EXTRA_BASE_URL="https://github.com/dobicinaitis/tailwind-cli-extra/releases/download/${TAILWIND_EXTRA_VERSION}/tailwindcss-extra"

CURL="$(command -v curl)"
if [ -z "$CURL" ]; then
    echo "'curl' not found, aborting" >&2
    exit 1
fi

_ARCH=$(uname -a | tr '[:upper:]' '[:lower:]')
case "$_ARCH" in
    *linux*x86_64*) ARCH_SPECIFIER="linux-x64" ;;
    *linux*arm64*) ARCH_SPECIFIER="linux-arm64" ;;
    *darwin*x86_64*) ARCH_SPECIFIER="macos-x64" ;;
    *darwin*arm64*) ARCH_SPECIFIER="macos-arm64" ;;
    *)
        echo "Unsupported platform '$(_ARCH)', aborting" >&2
        exit 1
        ;;
esac

echo "Downloading tailwindcss extra ${TAILWIND_EXTRA_VERSION} for ${ARCH_SPECIFIER}"
$CURL -sL ${TAILWIND_EXTRA_BASE_URL}-${ARCH_SPECIFIER} -o ./tailwindcss
chmod +x ./tailwindcss
