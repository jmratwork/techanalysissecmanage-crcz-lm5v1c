#!/bin/bash
set -euo pipefail

USE_SYSTEMCTL=1
if ! command -v systemctl >/dev/null 2>&1; then
    if [ "${DIRECT_START:-0}" -eq 1 ]; then
        USE_SYSTEMCTL=0
        echo "systemctl not found; using direct start mode" >&2
    else
        echo "systemctl command not found. Set DIRECT_START=1 to run without systemd." >&2
        exit 1
    fi
fi

MISP_PORT="${MISP_PORT:-8443}"

if [ -f /etc/misp/cti_feed.env ]; then
    # shellcheck disable=SC1091
    . /etc/misp/cti_feed.env
    export CTI_FEED_URL
fi

APT_UPDATED=0
apt_update_once() {
    if [ "$APT_UPDATED" -eq 0 ]; then
        export DEBIAN_FRONTEND=noninteractive
        if ! apt-get update -y; then
            echo "$(date) apt-get update failed" >&2
            return 1
        fi
        APT_UPDATED=1
    fi
}

install_deps() {
    if [ "${SKIP_INSTALL:-0}" -eq 1 ]; then
        return
    fi

    if ! command -v timeout >/dev/null 2>&1; then
        apt_update_once || true
        export DEBIAN_FRONTEND=noninteractive
        if ! apt-get install -y coreutils; then
            echo "$(date) failed to install coreutils via apt-get; trying local packages" >&2
            if ls /opt/offline/*.deb >/dev/null 2>&1; then
                if ! dpkg -i /opt/offline/*.deb; then
                    echo "$(date) failed to install local packages from /opt/offline" >&2
                    return 1
                fi
            else
                echo "$(date) no local packages found in /opt/offline" >&2
                return 1
            fi
        fi
    fi
}

check_port() {
    timeout 5 bash -c "cat < /dev/null > /dev/tcp/$1/$2"
}

start_misp() {
    mkdir -p /var/log/misp
    if [ "$USE_SYSTEMCTL" -eq 1 ]; then
        if systemctl is-active --quiet misp; then
            return 0
        fi
        if systemctl start misp >>/var/log/misp/service.log 2>&1; then
            if ! systemctl is-active --quiet misp; then
                echo "$(date) misp failed to start" >>/var/log/misp/service.log
                return 1
            fi
            check_port localhost "${MISP_PORT}" >>/var/log/misp/service.log 2>&1 || {
                echo "$(date) misp port check failed" >>/var/log/misp/service.log
                return 1
            }
        else
            echo "$(date) failed to run systemctl start misp" >>/var/log/misp/service.log
            return 1
        fi
    else
        if command -v service >/dev/null 2>&1; then
            if service misp start >>/var/log/misp/service.log 2>&1; then
                check_port localhost "${MISP_PORT}" >>/var/log/misp/service.log 2>&1 || {
                    echo "$(date) misp port check failed" >>/var/log/misp/service.log
                    return 1
                }
            else
                echo "$(date) failed to run service misp start" >>/var/log/misp/service.log
                return 1
            fi
        else
            if command -v misp-server >/dev/null 2>&1; then
                nohup misp-server >>/var/log/misp/service.log 2>&1 &
                sleep 1
                check_port localhost "${MISP_PORT}" >>/var/log/misp/service.log 2>&1 || {
                    echo "$(date) misp port check failed" >>/var/log/misp/service.log
                    return 1
                }
            else
                echo "$(date) service command and misp-server not found" >>/var/log/misp/service.log
                return 1
            fi
        fi
    fi
}

run_sharing_setup() {
    # configure MISP sharing settings
    mkdir -p /var/log/misp
    local script="$(dirname "$0")/../misp/sharing_setup.py"
    if [ -f "$script" ]; then
        if command -v python3 >/dev/null 2>&1; then
            python3 "$script" >>/var/log/misp/service.log 2>&1 || \
                echo "$(date) sharing setup failed" >>/var/log/misp/service.log
        else
            echo "$(date) python3 not found; skipping sharing setup" >>/var/log/misp/service.log
        fi
    fi
}

start_fetch_cti_feed() {
    mkdir -p /var/log/misp
    if [ "$USE_SYSTEMCTL" -eq 1 ]; then
        if systemctl is-active --quiet fetch-cti-feed; then
            return 0
        fi
        if systemctl start fetch-cti-feed >>/var/log/misp/service.log 2>&1; then
            if ! systemctl is-active --quiet fetch-cti-feed; then
                echo "$(date) fetch-cti-feed failed to start" >>/var/log/misp/service.log
                return 1
            fi
        else
            echo "$(date) failed to run systemctl start fetch-cti-feed" >>/var/log/misp/service.log
            return 1
        fi
    else
        if command -v service >/dev/null 2>&1; then
            if service fetch-cti-feed start >>/var/log/misp/service.log 2>&1; then
                true
            else
                echo "$(date) failed to run service fetch-cti-feed start" >>/var/log/misp/service.log
                return 1
            fi
        else
            if [ -f /opt/misp/fetch_cti_feed.sh ]; then
                nohup /opt/misp/fetch_cti_feed.sh >>/var/log/misp/service.log 2>&1 &
            else
                echo "$(date) service command and fetch_cti_feed.sh not found" >>/var/log/misp/service.log
                return 1
            fi
        fi
    fi
}

install_deps
start_misp
run_sharing_setup
start_fetch_cti_feed
