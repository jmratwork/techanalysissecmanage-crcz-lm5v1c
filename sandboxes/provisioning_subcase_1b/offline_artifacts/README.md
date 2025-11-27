This directory is intended to hold offline installation artefacts for the trainee workstation.

Expected contents:

- `apt/` - APT repository built with `dpkg-scanpackages` containing `.deb` packages for `nmap`, `gvm`, `python3-pip`, `git`, `curl`, `snapd`, and any dependencies.
- `pip/` - Python wheels for Caldera requirements, downloaded via `pip download`.
- `caldera.tar.gz` - Tarball of the MITRE Caldera source tree.
- `zaproxy.snap` - Snap package for OWASP ZAP.

Populate this directory using `download_offline_artifacts.sh` prior to running
`build_trainee_workstation.sh`.
