#!/bin/bash
set -e

APP_NAME="DouyinDownloader"
BUILD_DIR="/tmp/nuitka_build_$$"
OUT_DIR="$HOME/Desktop/$APP_NAME.app"

source .venv/bin/activate

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

.venv/bin/nuitka --standalone \
  --macos-create-app-bundle \
  --macos-app-name="$APP_NAME" \
  --macos-app-version="1.0" \
  --enable-plugin=tk-inter \
  --output-dir="$BUILD_DIR" \
  app.py || true

if [ -d "$BUILD_DIR/app.app" ]; then
  rm -rf "$OUT_DIR"
  mv "$BUILD_DIR/app.app" "$OUT_DIR"
  rm -rf "$BUILD_DIR"
  xattr -rc "$OUT_DIR" 2>/dev/null
  codesign --force --deep -s - "$OUT_DIR" 2>/dev/null
  echo "✅ 打包完成：$OUT_DIR"
else
  echo "❌ 构建失败"
  exit 1
fi
