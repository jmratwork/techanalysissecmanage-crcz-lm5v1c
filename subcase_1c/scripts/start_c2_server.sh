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

C2_BIND_IP="${C2_BIND_IP:-0.0.0.0}"
C2_PORT="${C2_PORT:-9001}"

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

    if ! command -v python3 >/dev/null 2>&1; then
        apt_update_once || return 1
        export DEBIAN_FRONTEND=noninteractive
        if ! apt-get install -y python3; then
            echo "$(date) failed to install python3" >&2
            return 1
        fi
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

setup_c2() {
    mkdir -p /opt/c2_server
    cp "$(dirname "$0")/c2_server.py" /opt/c2_server/c2_server.py

    if [ "$USE_SYSTEMCTL" -eq 1 ]; then
        cat >/etc/systemd/system/c2_server.service <<EOF
[Unit]
Description=Simple C2 Server
After=network.target

[Service]
Type=simple
Environment="C2_BIND_IP=${C2_BIND_IP}" "C2_PORT=${C2_PORT}"
ExecStart=/usr/bin/python3 /opt/c2_server/c2_server.py
Restart=on-failure
StandardOutput=append:/var/log/c2_server/c2_server.log
StandardError=append:/var/log/c2_server/c2_server.log
ExecStartPre=/bin/mkdir -p /var/log/c2_server

[Install]
WantedBy=multi-user.target
EOF

        systemctl daemon-reload
        systemctl enable c2_server.service >/dev/null 2>&1 || true
    fi
}

start_c2() {
    mkdir -p /var/log/c2_server
    if [ "$USE_SYSTEMCTL" -eq 1 ]; then
        if systemctl start c2_server.service >>/var/log/c2_server/service.log 2>&1; then
            if ! systemctl is-active --quiet c2_server.service; then
                echo "$(date) c2_server failed to start" >>/var/log/c2_server/service.log
                return 1
            fi
            check_port localhost "${C2_PORT}" >>/var/log/c2_server/service.log 2>&1 || {
                echo "$(date) c2_server port check failed" >>/var/log/c2_server/service.log
                return 1
            }
        else
            echo "$(date) failed to run systemctl start c2_server" >>/var/log/c2_server/service.log
            return 1
        fi
    else
        if command -v service >/dev/null 2>&1; then
            if service c2_server start >>/var/log/c2_server/service.log 2>&1; then
                check_port localhost "${C2_PORT}" >>/var/log/c2_server/service.log 2>&1 || {
                    echo "$(date) c2_server port check failed" >>/var/log/c2_server/service.log
                    return 1
                }
            else
                echo "$(date) failed to run service c2_server start" >>/var/log/c2_server/service.log
                return 1
            fi
        else
            nohup /usr/bin/python3 /opt/c2_server/c2_server.py >>/var/log/c2_server/service.log 2>&1 &
            sleep 1
            check_port localhost "${C2_PORT}" >>/var/log/c2_server/service.log 2>&1 || {
                echo "$(date) c2_server port check failed" >>/var/log/c2_server/service.log
                return 1
            }
        fi
    fi
}

install_deps
setup_c2
start_c2
