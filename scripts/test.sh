#!/usr/bin/env bash
# One entry point for local checks. CI runs the same checks natively.
# Uses Docker when docker-compose.yml exists; otherwise says what is missing.
set -euo pipefail
cd "$(dirname "$0")/.."

ran=0
if [ -f docker-compose.yml ] && command -v docker >/dev/null 2>&1; then
  [ -f .env ] || { [ -f .env.example ] && cp .env.example .env; } || true
  if [ -f backend/requirements.txt ]; then
    echo "== backend: lint + tests"
    docker compose run --rm backend sh -c \
      "(command -v ruff >/dev/null && ruff check . || true) && python manage.py makemigrations --check --dry-run && (command -v pytest >/dev/null && pytest -q || python manage.py test)"
    ran=1
  fi
  if [ -f frontend/package.json ]; then
    echo "== frontend: lint + tests + build"
    docker compose run --rm frontend sh -c \
      "npm run lint --if-present && npm run typecheck --if-present && CI=true npm run test --if-present && npm run build --if-present"
    ran=1
  fi
elif [ -f docker-compose.yml ]; then
  echo "Docker is not installed or not running. Start Docker Desktop, or rely on GitHub CI (./fc.sh ci)."
  exit 1
fi

[ "$ran" = 1 ] || echo "Nothing to test yet (no backend/ or frontend/ in the repo)."
