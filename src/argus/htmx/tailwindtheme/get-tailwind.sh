#! /usr/bin/env bash

cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null

TAILWIND_EXTRA_VERSION=$(cat VERSION)
TAILWIND_EXTRA_BASE_URL=https://github.com/dobicinaitis/tailwind-cli-extra/releases/download/${TAILWIND_EXTRA_VERSION}/tailwindcss-extra

case $(uname -a | tr '[:upper:]' '[:lower:]') in
    *linux*x86_64*) ARCH_SPECIFIER="linux-x64" ;;
    *linux*arm64*) ARCH_SPECIFIER="linux-arm64" ;;
    *darwin*x86_64*) ARCH_SPECIFIER="macos-x64" ;;
    *darwin*arm64*) ARCH_SPECIFIER="macos-arm64" ;;
    *)
        echo "Unsupported platform '$(uname -a)'"
        exit 1
        ;;
esac

echo "Downloading tailwindcss extra ${TAILWIND_EXTRA_VERSION} for ${ARCH_SPECIFIER}"
curl -sL ${TAILWIND_EXTRA_BASE_URL}-${ARCH_SPECIFIER} -o ./tailwindcss
chmod +x ./tailwindcss
