#!/usr/bin/env bash
# Builds examples/environment with repo2docker, then starts real user servers
# from it and from a Jupyter Docker Stacks image, and checks that both work.
# See tests/lib.sh for how tests are isolated. The repo2docker build itself
# downloads packages from the internet, as it would in CI.
# Needs ports 80, 443 and 3000. Do not run on a host that serves a real deployment.
cd "$(dirname "$0")/.."
source tests/lib.sh

# Same repo2docker version as the template's workflow.
R2D_IMAGE=$(grep -oE 'quay.io/jupyterhub/repo2docker:[^ ]+' examples/environment/.github/workflows/build.yml)
SERVER="https://$DOMAIN/user/$TEST_USER"

api() { curl -sk --resolve "$DOMAIN:443:127.0.0.1" -H "Authorization: token test-api-token" "$@"; }

# start_server <allowed_images key>: start the test user's server and wait for it.
start_server() {
  local response
  response=$(api -w ' HTTP %{http_code}' -X POST -d "{\"image\": \"$1\"}" "https://$DOMAIN/hub/api/users/$TEST_USER/server")
  case $response in
    *"HTTP 201" | *"HTTP 202") ;;
    *) echo "FAIL starting the $1 server: $response" >&2; return 1 ;;
  esac
  check "$1 server answers" returns 200 -H "Authorization: token test-api-token" "$SERVER/api/status"
}

stop_server() {
  api -X DELETE "https://$DOMAIN/hub/api/users/$TEST_USER/server" >/dev/null
  check "$1 server stops" container_gone
}

container_gone() { ! docker inspect "jupyter-$TEST_USER" >/dev/null 2>&1; }

# Names in the server's starting folder.
start_folder() {
  local listing
  listing=$(api "$SERVER/api/contents/")
  grep -oE '"name": ?"[^"]+"' <<<"$listing" | cut -d'"' -f4
}

starts_with_singleuser() {
  docker inspect "jupyter-$TEST_USER" --format '{{json .Config.Cmd}}' | grep -q '"jupyterhub-singleuser"'
}
shows_repository_files() { start_folder | grep -qw environment.yml && start_folder | grep -qw work; }
work_is_writable() { docker exec "jupyter-$TEST_USER" sh -c 'echo test > ~/work/written-by-test.txt'; }
opens_in_work() { start_folder | grep -qw written-by-test.txt && ! start_folder | grep -qw environment.yml; }

docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$(pwd -W 2>/dev/null || pwd)/examples/environment:/repo:ro" "$R2D_IMAGE" \
  jupyter-repo2docker --no-run --user-name jovyan --user-id 1000 \
  --image-name jupyterhub-test-environment:local /repo

compose up --detach --build --wait
api -X POST "https://$DOMAIN/hub/api/users/$TEST_USER" >/dev/null

start_server environment
check "repo2docker server runs jupyterhub-singleuser" starts_with_singleuser
check "repository files are next to work/" shows_repository_files
check "work/ is writable" work_is_writable
stop_server environment

start_server docker-stacks
check "Docker Stacks server opens in work/" opens_in_work
stop_server docker-stacks

assert_no_outside_lookups
