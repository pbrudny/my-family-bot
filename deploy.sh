#!/bin/bash
# Usage:
#   ./deploy.sh           — deploy both
#   ./deploy.sh backend   — deploy backend only
#   ./deploy.sh frontend  — deploy frontend only
set -euo pipefail

DOKKU_HOST="pbrudny.tojest.dev"
TARGET="${1:-both}"

deploy_backend() {
    echo "==> Deploying backend..."
    git push dokku main
    echo "==> Backend deployed: http://myfamily.toadres.pl"
}

deploy_frontend() {
    echo "==> Building frontend image..."
    docker build -f Dockerfile.frontend -t family-bot-frontend:latest .
    echo "==> Transferring image to $DOKKU_HOST and deploying..."
    docker save family-bot-frontend:latest \
        | ssh root@"$DOKKU_HOST" \
          "docker load && dokku git:from-image family-bot-frontend family-bot-frontend:latest"
    echo "==> Frontend deployed: http://app.myfamily.toadres.pl"
}

case "$TARGET" in
    backend)  deploy_backend  ;;
    frontend) deploy_frontend ;;
    both)     deploy_backend && deploy_frontend ;;
    *)
        echo "Usage: ./deploy.sh [backend|frontend|both]"
        exit 1
        ;;
esac
