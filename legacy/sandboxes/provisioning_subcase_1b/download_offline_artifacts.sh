#!/bin/bash
set -e

# Script to pre-download packages for the trainee workstation.
# All artefacts are stored under offline_artifacts/ relative to this script.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARTIFACTS_DIR="${SCRIPT_DIR}/offline_artifacts"
APT_DIR="${ARTIFACTS_DIR}/apt"
PIP_DIR="${ARTIFACTS_DIR}/pip"

mkdir -p "$APT_DIR" "$PIP_DIR"

# Download APT packages
# Requires internet access and dpkg-dev for dpkg-scanpackages
apt-get update
apt-get install -y --no-install-recommends dpkg-dev
apt-get download nmap gvm python3-pip git curl snapd
mv -- *.deb "$APT_DIR"/
(
    cd "$APT_DIR"
    dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz
)

# Download OWASP ZAP snap
snap download zaproxy --basename zaproxy
mv zaproxy.snap "$ARTIFACTS_DIR"/

# Download Caldera and its Python dependencies
CALDERA_TMP=$(mktemp -d)
trap 'rm -rf "$CALDERA_TMP"' EXIT

git clone https://github.com/mitre/caldera "$CALDERA_TMP/caldera"
# Create tarball of Caldera
(tar -czf "$ARTIFACTS_DIR/caldera.tar.gz" -C "$CALDERA_TMP" caldera)
# Download Python requirements as wheels
pip3 download -r "$CALDERA_TMP/caldera/requirements.txt" -d "$PIP_DIR"
