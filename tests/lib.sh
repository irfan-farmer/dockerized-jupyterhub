# shellcheck shell=bash
# Shared setup for the test scripts. Source it from the repository root.
#
# The tests start the whole stack with the placeholder settings in
# tests/test.env. Containers look up outside names through a canary resolver
# (see tests/compose.test.yaml), so tests never contact a real server.
# Containers and volumes are removed when the script exits.
set -euo pipefail
# Git Bash on Windows would otherwise rewrite container paths like /etc/...
export MSYS_NO_PATHCONV=1
# ...which also means its curl, a Windows program, needs NUL for /dev/null.
DEVNULL=/dev/null
if [ -n "${MSYSTEM:-}" ]; then DEVNULL=NUL; fi

set -a
source tests/test.env
set +a

if [ -n "$(docker ps --quiet --filter label=com.docker.compose.project=jupyterhub)" ]; then
  echo "A JupyterHub deployment is running on this host. Not running tests." >&2
  exit 1
fi

# The user tests start servers for. Its unusual name keeps the cleanup below
# from touching a real user's container or volume.
TEST_USER=smoketestuser

compose() {
  docker compose --project-name jupyterhub-test --env-file tests/test.env \
    -f compose.yaml -f tests/compose.test.yaml "$@"
}

cleanup() {
  local code=$?
  if [ "$code" -ne 0 ]; then compose logs --no-color --tail 40; fi
  docker rm --force "jupyter-$TEST_USER" >/dev/null 2>&1 || true
  compose down --volumes --remove-orphans
  docker volume rm "jupyterhub-user-$TEST_USER" >/dev/null 2>&1 || true
  exit "$code"
}
trap cleanup EXIT

# returns <status> <curl arguments>: requests to $DOMAIN go to this machine,
# and -k accepts Traefik's default certificate, as tests request none.
returns() {
  local expected=$1
  shift
  [ "$(curl -sk -o "$DEVNULL" -w '%{http_code}' --resolve "$DOMAIN:443:127.0.0.1" "$@")" = "$expected" ]
}

# Retry a check for up to a minute.
check() {
  local name=$1
  shift
  for _ in $(seq 30); do
    if "$@"; then
      echo "ok   $name"
      return 0
    fi
    sleep 2
  done
  echo "FAIL $name" >&2
  return 1
}

# Fail if the canary resolver was asked for any name other than .invalid
# names, which never resolve anywhere.
assert_no_outside_lookups() {
  local log leaked
  log=$(compose logs --no-log-prefix canary-dns)
  leaked=$(grep -oE '"[A-Z]+ IN [^ ]+' <<<"$log" | awk '{print $3}' | grep -v '\.invalid\.$' | sort -u || true)
  if [ -n "$leaked" ]; then
    echo "FAIL names looked up outside Docker:" $leaked >&2
    return 1
  fi
  echo "ok   no name was looked up outside Docker"
}
