#!/usr/bin/env bash
# Starts the whole stack and checks that every part answers, including while
# services are stopped. See tests/lib.sh for how tests are isolated.
# Needs ports 80, 443 and 3000. Do not run on a host that serves a real deployment.
cd "$(dirname "$0")/.."
source tests/lib.sh

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
curl -sk --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN/" >/dev/null || true
curl -s -u "admin:$GRAFANA_ADMIN_PASSWORD" \
  http://127.0.0.1:3000/api/datasources/uid/prometheus/health >/dev/null || true
sleep 10
compose up --detach --wait proxy maintenance prometheus
check "hub answers after the proxy restarts" returns 200 "https://$DOMAIN/hub/health"

assert_no_outside_lookups
