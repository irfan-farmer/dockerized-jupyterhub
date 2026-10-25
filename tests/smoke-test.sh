#!/usr/bin/env bash
# Starts the whole stack with the placeholder settings in tests/test.env and
# checks that every part answers. Containers look up outside names through a
# canary resolver (see tests/compose.test.yaml), so the test never contacts a
# real server and fails if any name is looked up outside Docker.
# Removes its containers and volumes afterwards.
# Needs ports 80, 443 and 3000. Do not run on a host that serves a real deployment.
set -euo pipefail
cd "$(dirname "$0")/.."
# Git Bash on Windows would otherwise rewrite container paths like /etc/...
export MSYS_NO_PATHCONV=1

set -a
source tests/test.env
set +a

if [ -n "$(docker ps --quiet --filter label=com.docker.compose.project=jupyterhub)" ]; then
  echo "A JupyterHub deployment is running on this host. Not running tests." >&2
  exit 1
fi

compose() {
  docker compose --project-name jupyterhub-test --env-file tests/test.env \
    -f compose.yaml -f tests/compose.test.yaml "$@"
}

cleanup() {
  local code=$?
  if [ "$code" -ne 0 ]; then compose logs --no-color --tail 40; fi
  compose down --volumes --remove-orphans
  exit "$code"
}
trap cleanup EXIT

# returns <status> <curl arguments>: requests to $DOMAIN go to this machine,
# and -k accepts Traefik's default certificate, as tests request none.
returns() {
  local expected=$1
  shift
  [ "$(curl -sk -o /dev/null -w '%{http_code}' --resolve "$DOMAIN:443:127.0.0.1" "$@")" = "$expected" ]
}

# Responses are captured before grep: piping curl into `grep -q` fails under
# pipefail when grep exits before curl has finished writing.
redirects_to_https() {
  local headers
  headers=$(curl -sI --resolve "$DOMAIN:80:127.0.0.1" "http://$DOMAIN/")
  grep -qi '^location: https://' <<<"$headers"
}

login_page_shows_provider() {
  local page
  page=$(curl -sk --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN/hub/login")
  grep -q 'Sign in with SSO' <<<"$page"
}

all_targets_up() {
  local targets
  targets=$(compose exec -T prometheus wget -qO- http://localhost:9090/api/v1/targets)
  [ "$(grep -o '"health":"up"' <<<"$targets" | wc -l)" -eq 4 ]
}

# Names the canary resolver was asked for, except .invalid names, which never
# resolve anywhere.
outside_lookups() {
  local log
  log=$(compose logs --no-log-prefix canary-dns)
  grep -oE '"[A-Z]+ IN [^ ]+' <<<"$log" | awk '{print $3}' | grep -v '\.invalid\.$' | sort -u || true
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

compose run --rm --no-deps --entrypoint promtool prometheus check config /etc/prometheus/prometheus.yml
compose up --detach --build --wait

check "hub answers through Traefik" returns 200 "https://$DOMAIN/hub/health"
check "HTTP redirects to HTTPS" redirects_to_https
check "login page offers the identity provider" login_page_shows_provider
check "Grafana answers on localhost" returns 200 http://127.0.0.1:3000/api/health
check "Grafana dashboard is provisioned" returns 200 -u "admin:$GRAFANA_ADMIN_PASSWORD" \
  http://127.0.0.1:3000/api/dashboards/uid/jupyterhub
check "Prometheus scrapes all targets" all_targets_up

compose stop jupyterhub
check "maintenance page while the hub is stopped" returns 503 "https://$DOMAIN/"
check "users' traffic still reaches the proxy" returns 200 "https://$DOMAIN/_chp_healthz"

compose up --detach --wait jupyterhub
check "hub is back after a restart" returns 200 "https://$DOMAIN/hub/health"

# Stop the other services that are reached by name, make Traefik and Grafana
# look for them, then start them again.
compose stop proxy maintenance prometheus
curl -sk -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN/" || true
curl -s -o /dev/null -u "admin:$GRAFANA_ADMIN_PASSWORD" \
  http://127.0.0.1:3000/api/datasources/uid/prometheus/health || true
sleep 10
compose up --detach --wait proxy maintenance prometheus
check "hub answers after the proxy restarts" returns 200 "https://$DOMAIN/hub/health"

leaked=$(outside_lookups)
if [ -n "$leaked" ]; then
  echo "FAIL names looked up outside Docker:" $leaked >&2
  exit 1
fi
echo "ok   no name was looked up outside Docker"
