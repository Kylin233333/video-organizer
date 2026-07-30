#!/bin/bash
set -e

source .venv/bin/activate

APP_NAME="抖音视频批量下载"

nuitka --standalone \
  --macos-create-app-bundle \
  --macos-app-name="$APP_NAME" \
  --macos-app-version="1.0" \
  --enable-plugin=tk-inter \
  --output-dir=dist \
  app.py

# 清理扩展属性并重新签名（macOS 14+ 必需）
sudo xattr -rc "dist/$APP_NAME.app" 2>/dev/null
codesign --force --deep -s - "dist/$APP_NAME.app" 2>/dev/null

echo ""
echo "✅ 打包完成：dist/$APP_NAME.app"
