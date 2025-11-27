#!/bin/bash
set -e

# Example provisioning steps for the trainee workstation VM

###############################################################################
# Offline installation paths
###############################################################################
# The image this script runs on is expected to ship with all required tooling
# already downloaded to a local directory.  By default we look for the
# artefacts next to this script under "offline_artifacts" but the location can
# be overridden via the ARTIFACTS_DIR environment variable.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARTIFACTS_DIR="${ARTIFACTS_DIR:-${SCRIPT_DIR}/offline_artifacts}"
APT_REPO="${ARTIFACTS_DIR}/apt"
PIP_REPO="${ARTIFACTS_DIR}/pip"
NMAP_DEB="${ARTIFACTS_DIR}/apt/nmap_7.93+dfsg1-1_amd64.deb"
GVM_DEB="${ARTIFACTS_DIR}/apt/gvm_25.04.0_all.deb"
CALDERA_ARCHIVE="${ARTIFACTS_DIR}/caldera-5.3.0.tar.gz"
ZAP_SNAP="${ARTIFACTS_DIR}/zaproxy_2.16.1_amd64.snap"

NMAP_SHA256="1ac65a0a1038ffa8de7ee13a146c4cbb9dac3180c7faef703f3efb3adad098b2"
GVM_SHA256="19b450baabf0a916f591fe786c71fa46db786d21132c5f711b225b8f32b14fe9"
CALDERA_SHA256="23f79e83ccf6215bac627f96bed303f09b1759f524a151608279b08574c5eff1"
ZAP_SNAP_SHA256="a980e67ae3b8ae6d05165aeb8376014985fda9c2159c4122bec533abab555148"

# Sanity check that artefacts are present
for path in "$APT_REPO" "$PIP_REPO" "$NMAP_DEB" "$GVM_DEB" "$CALDERA_ARCHIVE" "$ZAP_SNAP"; do
    if [ ! -e "$path" ]; then
        echo "Required artefact $path not found" >&2
        exit 1
    fi
done

# Verify artefact integrity
echo "${NMAP_SHA256}  ${NMAP_DEB}" | sha256sum -c -
echo "${GVM_SHA256}  ${GVM_DEB}" | sha256sum -c -
echo "${CALDERA_SHA256}  ${CALDERA_ARCHIVE}" | sha256sum -c -
echo "${ZAP_SNAP_SHA256}  ${ZAP_SNAP}" | sha256sum -c -

###############################################################################
# Approved tooling list
###############################################################################
ALLOWED_TOOLS=(nmap zaproxy gvm caldera)
TOOLS_TO_INSTALL=(nmap zaproxy gvm caldera)

for tool in "${TOOLS_TO_INSTALL[@]}"; do
    if [[ ! " ${ALLOWED_TOOLS[*]} " =~ ${tool} ]]; then
        echo "Tool ${tool} is not in the allowed list" >&2
        exit 1
    fi
done

###############################################################################
# Configure local APT repository and install base packages
###############################################################################
echo "deb [trusted=yes] file:${APT_REPO} ./" >/etc/apt/sources.list.d/offline.list
apt-get update
apt-get install -y --no-install-recommends python3-pip git curl snapd

# Install tool packages from verified artefacts
dpkg -i "${NMAP_DEB}" "${GVM_DEB}" || apt-get install -f -y --no-install-recommends

###############################################################################
# Install OWASP ZAP from local snap file
###############################################################################
if ! command -v snap >/dev/null 2>&1; then
    echo "snapd failed to install" >&2
    exit 1
fi
systemctl enable --now snapd.socket
ln -sf /var/lib/snapd/snap /snap
snap install --dangerous "${ZAP_SNAP}" --classic

###############################################################################
# Configure and verify OpenVAS (Greenbone)
###############################################################################
gvm-setup
gvm-start
for _ in {1..30}; do
    if curl -k -sSf https://127.0.0.1:9392 >/dev/null 2>&1; then
        break
    fi
    sleep 1
done
curl -k -sSf https://127.0.0.1:9392 >/dev/null 2>&1
gvm-stop

###############################################################################
# Launch ZAP in daemon mode to verify availability
###############################################################################
zaproxy -daemon -port 8090 -host 127.0.0.1 &
ZAP_PID=$!
for _ in {1..30}; do
    if curl -sSf http://127.0.0.1:8090/ >/dev/null 2>&1; then
        break
    fi
    sleep 1
done
curl -sSf http://127.0.0.1:8090/ >/dev/null 2>&1
zaproxy -cmd -shutdown >/dev/null 2>&1 || kill "$ZAP_PID" || true

###############################################################################
# Install MITRE Caldera from local artefacts
###############################################################################
if [ ! -d /opt/caldera ]; then
    mkdir -p /opt
    tar -xf "${CALDERA_ARCHIVE}" -C /opt
    pip3 install --no-index --find-links "${PIP_REPO}" -r /opt/caldera/requirements.txt
fi

###############################################################################
# Verify each tool runs without missing dependencies
###############################################################################
nmap --version >/dev/null
zaproxy --version >/dev/null 2>&1 || zaproxy -version >/dev/null 2>&1
gvm-manage-certs --version >/dev/null 2>&1 || gvmd --version >/dev/null 2>&1
python3 /opt/caldera/server.py --help >/dev/null 2>&1
