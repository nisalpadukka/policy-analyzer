#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$SCRIPT_DIR/../../api"
OUTPUT_ZIP="$SCRIPT_DIR/lambda_function.zip"
PYTHON_VERSION="3.12"

echo "Building Lambda package for Linux"

cd "$API_DIR"

echo "Installing dependencies locally..."
rm -rf package "$OUTPUT_ZIP"  # Clean up before building
mkdir -p package
python3 -m pip install \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version ${PYTHON_VERSION} \
  --only-binary=:all: \
  -t package/ \
  -r requirements.txt \
  --upgrade --no-cache-dir

cp lambda_function.py package/
echo "Creating zip file..."
cd package
zip -r "$OUTPUT_ZIP" . -q
cd ..
rm -rf package  # Clean up package directory after zipping
echo "Lambda package ready: $OUTPUT_ZIP"

