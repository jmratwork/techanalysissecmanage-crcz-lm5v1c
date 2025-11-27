#!/usr/bin/env bash
# Create an Open edX cohort, generate invite codes, and register participants with KYPO.
# Usage: subcase_1b/scripts/enrol_instructor.sh COURSE_ID email1 [email2 ...]
# Required environment variables:
#   OPENEDX_TOKEN            - Token with permissions to manage cohorts in Open edX.
#   TRAINING_PLATFORM_USER   - Username of the instructor account in the training platform.
#   TRAINING_PLATFORM_PASS   - Password for the instructor account.
# Optional environment variables:
#   OPENEDX_API              - Base URL of the Open edX instance (default: http://localhost:18000).
#   INVITES_API              - Base URL of the training platform (default: http://localhost:5000).
#   COHORT_NAME              - Name for the cohort to create (default: instructors).
#   KYPO_API                 - Base URL of KYPO API; if empty a list file is used instead.
#   KYPO_LIST_FILE           - File used when KYPO_API is not set (default: kypo_participants.txt).
#   MAIL_CMD                 - Command to send invite codes by email (e.g. "mail -s 'Invite'").

set -euo pipefail

OPENEDX_API="${OPENEDX_API:-http://localhost:18000}"
OPENEDX_TOKEN="${OPENEDX_TOKEN:?Open edX token not set}"
INVITES_API="${INVITES_API:-http://localhost:5000}"
COHORT_NAME="${COHORT_NAME:-instructors}"
KYPO_API="${KYPO_API:-}"
KYPO_LIST_FILE="${KYPO_LIST_FILE:-kypo_participants.txt}"
TRAINING_PLATFORM_USER="${TRAINING_PLATFORM_USER:?Training platform username not set}"
TRAINING_PLATFORM_PASS="${TRAINING_PLATFORM_PASS:?Training platform password not set}"

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 COURSE_ID email..." >&2
  exit 1
fi

course_id=$1
shift

# Obtain a token from the training platform for inviting instructors
invites_token=$(TRAINING_PLATFORM_URL="${INVITES_API}" \
  python subcase_1b/training_platform/cli.py login \
    --username "${TRAINING_PLATFORM_USER}" \
    --password "${TRAINING_PLATFORM_PASS}" | tr -d '\r\n')

if [ -z "${invites_token:-}" ]; then
  echo "Failed to obtain training platform token" >&2
  exit 1
fi

# Create cohort
curl -sS -X POST "${OPENEDX_API}/api/cohorts/" \
  -H "Authorization: Bearer ${OPENEDX_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"${COHORT_NAME}\", \"course_id\": \"${course_id}\"}" >/dev/null

for email in "$@"; do
  # Generate invite code
  response=$(curl -sS -X POST "${INVITES_API}/invites" \
      -H "Content-Type: application/json" \
      -d "{\"token\": \"${invites_token}\", \"course_id\": \"${course_id}\", \"email\": \"${email}\"}" \
      -w '\n%{http_code}')

  http_code=$(printf '%s' "$response" | tail -n1)
  body=$(printf '%s' "$response" | sed '$d')

  if [ "$http_code" -ne 200 ]; then
    echo "Failed to invite ${email}: HTTP ${http_code}" >&2
    if [ -n "$body" ]; then
      echo "$body" >&2
    fi
    exit 1
  fi

  invite_code=$(printf '%s' "$body" | python -c 'import sys, json; data=json.load(sys.stdin); print(data.get("invite_code", ""))')

  if [ -z "$invite_code" ]; then
    echo "Invite code missing from response for ${email}" >&2
    if [ -n "$body" ]; then
      echo "$body" >&2
    fi
    exit 1
  fi

  if [ -n "${MAIL_CMD:-}" ]; then
    printf 'Invite code: %s\n' "$invite_code" | ${MAIL_CMD} "$email"
  else
    echo "$email: $invite_code"
  fi

  if [ -n "$KYPO_API" ]; then
    curl -sS -X POST "${KYPO_API}/participants" \
      -H "Content-Type: application/json" \
      -d "{\"email\": \"${email}\", \"course_id\": \"${course_id}\"}" >/dev/null
  else
    echo "$email" >> "$KYPO_LIST_FILE"
  fi
done
