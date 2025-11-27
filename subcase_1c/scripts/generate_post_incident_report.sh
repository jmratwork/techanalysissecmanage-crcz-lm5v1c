#!/bin/bash
set -euo pipefail

# Determine repository root
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPORT_DIR="$REPO_ROOT/reports"
TIMESTAMP="${TIMESTAMP_OVERRIDE:-$(date +%Y%m%d_%H%M%S)}"
REPORT_MD="$REPORT_DIR/post_incident_report_$TIMESTAMP.md"
REPORT_HTML="$REPORT_DIR/post_incident_report_$TIMESTAMP.html"

# Default log locations (can be overridden by environment variables)
NG_SIEM_LOG=${NG_SIEM_LOG:-/var/log/ngsiem.log}
BIPS_LOG=${BIPS_LOG:-/var/log/bips.log}
ACT_LOG=${ACT_LOG:-/var/log/act.log}

mkdir -p "$REPORT_DIR"

# Extract lines matching a pattern from a log file
extract_info() {
  local label="$1"; local log="$2"; local pattern="$3"
  echo "### $label"
  if [[ -f "$log" ]]; then
    local matches
    matches=$(grep -iE "$pattern" "$log" || true)
    if [[ -n "$matches" ]]; then
      echo "$matches"
    else
      echo "No relevant entries found."
    fi
  else
    echo "Log file $log not found."
  fi
  echo ""
}

# Convert a log into a Markdown code block
collect_log() {
  local name="$1"; local path="$2"
  echo "### $name Logs ($path)"
  if [[ -f "$path" ]]; then
    echo '```'
    tail -n 100 "$path"
    echo '```'
  else
    echo "_Logs not found at $path._"
  fi
  echo ""
}

{
  echo "# Post-Incident Report - $TIMESTAMP"
  echo ""
  echo "## Summary"
  extract_info "Input Vectors" "$NG_SIEM_LOG" "vector|entry"
  extract_info "Lateral Movements" "$ACT_LOG" "lateral"
  extract_info "Mitigation Times" "$BIPS_LOG" "mitigat|patch|contain"

  section_list() {
    local title="$1"; local log="$2"; local pattern="$3"
    echo "## $title"
    if [[ -f "$log" ]]; then
      local matches
      matches=$(grep -iE "$pattern" "$log" || true)
      if [[ -n "$matches" ]]; then
        echo "$matches" | sed 's/^/- /'
      else
        echo "- None found."
      fi
    else
      echo "- Log file $log not found."
    fi
    echo ""
  }

  section_list "Findings" "$NG_SIEM_LOG" "FINDING|ALERT"
  section_list "Containment Actions" "$ACT_LOG" "contain|mitigat|block"
  section_list "Recommendations" "$BIPS_LOG" "recommend|advice|patch"

  echo "## Logs"
  collect_log "NG-SIEM" "$NG_SIEM_LOG"
  collect_log "BIPS" "$BIPS_LOG"
  collect_log "Act" "$ACT_LOG"
} > "$REPORT_MD"

# Convert Markdown report to HTML
if python3 -c "import markdown" 2>/dev/null; then
  python3 <<'PY' "$REPORT_MD" "$REPORT_HTML"
import sys, markdown, io
md_path, html_path = sys.argv[1], sys.argv[2]
with open(md_path, 'r') as f:
    text = f.read()
html = markdown.markdown(text)
with open(html_path, 'w') as f:
    f.write(html)
PY
else
  html_escaped=$(sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g' "$REPORT_MD")
  printf '<html><body><pre>%s</pre></body></html>' "$html_escaped" > "$REPORT_HTML"
fi

echo "Report generated at $REPORT_MD and $REPORT_HTML"
