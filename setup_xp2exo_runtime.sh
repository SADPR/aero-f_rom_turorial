#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ROOT="$REPO_ROOT/.xp2exo_runtime"
DEB_DIR="$RUNTIME_ROOT/debs"
EXTRACT_DIR="$RUNTIME_ROOT/extract"
LIB_DIR="$RUNTIME_ROOT/lib"

PACKAGES=(
  libexodusii5
  libnetcdf-mpi-19
  libhdf5-openmpi-103-1t64
  libhdf5-openmpi-hl-100t64
)

for cmd in apt dpkg-deb; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $cmd"
    exit 1
  fi
done

mkdir -p "$DEB_DIR"
rm -rf "$EXTRACT_DIR" "$LIB_DIR"
mkdir -p "$EXTRACT_DIR" "$LIB_DIR"

echo "Downloading runtime packages..."
for pkg in "${PACKAGES[@]}"; do
  echo "  - $pkg"
  (
    cd "$DEB_DIR"
    apt download "$pkg" >/dev/null
  )
done

echo "Extracting libraries..."
for deb in "$DEB_DIR"/*.deb; do
  dpkg-deb -x "$deb" "$EXTRACT_DIR"
done

SRC_LIB_DIR="$EXTRACT_DIR/usr/lib/x86_64-linux-gnu"
if [[ ! -d "$SRC_LIB_DIR" ]]; then
  echo "ERROR: extracted library directory not found: $SRC_LIB_DIR"
  exit 1
fi

cp -a "$SRC_LIB_DIR"/libexoIIv2c.so* "$LIB_DIR"/ 2>/dev/null || true
cp -a "$SRC_LIB_DIR"/libnetcdf_mpi.so* "$LIB_DIR"/ 2>/dev/null || true
cp -a "$SRC_LIB_DIR"/libhdf5_openmpi*.so* "$LIB_DIR"/ 2>/dev/null || true
cp -a "$SRC_LIB_DIR"/libhdf5_serial*.so* "$LIB_DIR"/ 2>/dev/null || true
cp -a "$SRC_LIB_DIR"/libmpi*.so* "$LIB_DIR"/ 2>/dev/null || true
cp -a "$SRC_LIB_DIR"/libopen-rte*.so* "$LIB_DIR"/ 2>/dev/null || true
cp -a "$SRC_LIB_DIR"/libopen-pal*.so* "$LIB_DIR"/ 2>/dev/null || true

if [[ -f "$LIB_DIR/libexoIIv2c.so.5" ]]; then
  ln -sf libexoIIv2c.so.5 "$LIB_DIR/libexodus.so.2"
elif [[ -f "$LIB_DIR/libexoIIv2c.so.5.14.0" ]]; then
  ln -sf libexoIIv2c.so.5.14.0 "$LIB_DIR/libexodus.so.2"
else
  echo "ERROR: could not locate libexoIIv2c in $LIB_DIR"
  exit 1
fi

if [[ -f /usr/lib/x86_64-linux-gnu/libnetcdf.so.19 ]]; then
  ln -sf /usr/lib/x86_64-linux-gnu/libnetcdf.so.19 "$LIB_DIR/libnetcdf.so.19"
  ln -sf libnetcdf.so.19 "$LIB_DIR/libnetcdf.so.11"
elif [[ -f "$LIB_DIR/libnetcdf_mpi.so.19" ]]; then
  ln -sf libnetcdf_mpi.so.19 "$LIB_DIR/libnetcdf.so.11"
else
  echo "ERROR: could not locate libnetcdf runtime to provide libnetcdf.so.11"
  exit 1
fi

echo
printf 'xp2exo compatibility runtime ready at:\n  %s\n' "$LIB_DIR"
printf 'It will be auto-used by simulations/*/xp2exo.sh scripts.\n'
