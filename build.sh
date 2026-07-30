#!/bin/bash
set -e

APP_NAME="抖音视频批量下载"

# 清理项目及依赖中的扩展属性，避免 Nuitka 内部 codesign 失败
sudo xattr -rc .venv . 2>/dev/null

source .venv/bin/activate

nuitka --standalone \
  --macos-create-app-bundle \
  --macos-app-name="$APP_NAME" \
  --macos-app-version="1.0" \
  --enable-plugin=tk-inter \
  --output-dir=dist \
  app.py || true

# 重命名并重新签名
if [ -d "dist/app.app" ]; then
  mv "dist/app.app" "dist/$APP_NAME.app" 2>/dev/null
  sudo xattr -rc "dist/$APP_NAME.app" 2>/dev/null
  codesign --force --deep -s - "dist/$APP_NAME.app" 2>/dev/null && \
    echo "✅ 签名成功"
fi

echo "✅ 打包完成：dist/$APP_NAME.app"
