#!/usr/bin/env bash
# Bundled shared libs for Playwright Chromium on WSL (no sudo).
set -euo pipefail
LIBDIR="$(cd "$(dirname "$0")/.lib" && pwd)"
cd "$LIBDIR"
pkgs=(
  libgbm1 libxkbcommon0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0
  libcups2 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2
  libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 libwayland-client0
  libwayland-server0 libx11-6 libxcb1 libxext6 libglib2.0-0 libdbus-1-3
  libexpat1 libfontconfig1 libfreetype6 libpixman-1-0
)
apt-get download "${pkgs[@]}"
rm -rf extracted && mkdir extracted
for deb in *.deb; do dpkg-deb -x "$deb" extracted; done
echo "OK — libs in $LIBDIR/extracted"
