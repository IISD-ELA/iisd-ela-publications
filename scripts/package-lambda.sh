#!/bin/bash
set -eo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build"
PACKAGE_DIR="$BUILD_DIR/package"
ZIP_PATH="$BUILD_DIR/lambda.zip"
IMAGE="public.ecr.aws/lambda/python:3.14"

rm -rf "$PACKAGE_DIR" "$ZIP_PATH"
mkdir -p "$PACKAGE_DIR"

docker run --rm \
  --platform linux/amd64 \
  --entrypoint /bin/bash \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -e PIP_CACHE_DIR=/tmp/pip-cache \
  -v /etc/passwd:/etc/passwd:ro \
  -v /etc/group:/etc/group:ro \
  -v "$ROOT_DIR:/src:ro" \
  -v "$BUILD_DIR:/out" \
  "$IMAGE" \
  -lc 'set -eo pipefail
python -m pip install --no-cache-dir --target /out/package -r /src/requirements-lambda.txt
cp -R /src/src/publications_app /out/package/
python - <<'"'"'PY'"'"'
import shutil
from pathlib import Path

root = Path("/out/package")
for path in root.rglob("__pycache__"):
    if path.is_dir():
        shutil.rmtree(path)
for path in root.rglob("*"):
    if path.suffix in (".pyc", ".pyo"):
        path.unlink()
PY'

python3 - "$PACKAGE_DIR" "$ZIP_PATH" <<'PY'
import os
import sys
import zipfile

package_dir, zip_path = sys.argv[1:3]

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
    for root, _, files in os.walk(package_dir):
        for name in files:
            path = os.path.join(root, name)
            relative_path = os.path.relpath(path, package_dir)
            archive.write(path, relative_path)
PY

du -sh "$PACKAGE_DIR"
ls -lh "$ZIP_PATH"
