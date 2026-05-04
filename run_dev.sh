#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

CLEAN=0
for arg in "$@"; do
    case "$arg" in
        --clean)
            CLEAN=1
            ;;
        -h|--help)
            cat <<EOF
Usage: ./run_dev.sh [--clean]

  --clean    Drop the PostgreSQL volume, rebuild the database from scratch,
             and seed the ICF (International Crane Foundation) demo data.
EOF
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            echo "Run './run_dev.sh --help' for usage." >&2
            exit 2
            ;;
    esac
done

echo "=== Crane Development Server ==="

# 0. Ensure Tailwind standalone binary exists, then build CSS
TAILWIND_BIN="$PROJECT_DIR/bin/tailwindcss"
if [ ! -x "$TAILWIND_BIN" ]; then
    echo "Downloading Tailwind standalone binary..."
    mkdir -p "$PROJECT_DIR/bin"
    curl -sL https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64 \
        -o "$TAILWIND_BIN"
    chmod +x "$TAILWIND_BIN"
fi
echo "Building CSS..."
"$TAILWIND_BIN" -i "$PROJECT_DIR/static/css/crane.src.css" \
                -o "$PROJECT_DIR/static/css/crane.css" \
                --minify 2>&1 | grep -v '^≈' || true

# 0.1 Use PostgreSQL via Docker (port 5433)
export DATABASE_URL="${DATABASE_URL:-postgres://crane:crane@localhost:5433/crane}"

# Optional clean reset: drop volume so PostgreSQL comes back empty
if [ "$CLEAN" -eq 1 ]; then
    if ! command -v docker &> /dev/null; then
        echo "Docker is required for --clean but was not found in PATH." >&2
        exit 1
    fi
    echo "Resetting PostgreSQL volume (--clean)..."
    docker compose -f "$PROJECT_DIR/docker-compose.yml" down -v
fi

# Ensure PostgreSQL container is running
if command -v docker &> /dev/null; then
    if ! docker compose -f "$PROJECT_DIR/docker-compose.yml" ps db --status running -q 2>/dev/null | grep -q .; then
        echo "Starting PostgreSQL..."
        docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d db
        # Wait until Postgres is ready to accept connections
        for _ in $(seq 1 30); do
            if docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T db pg_isready -U crane -d crane >/dev/null 2>&1; then
                break
            fi
            sleep 1
        done
    fi
fi

# 1. Ensure virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# 2. Activate venv
source "$VENV_DIR/bin/activate"

# 3. Install/update dependencies
echo "Installing dependencies..."
pip install -q -r "$PROJECT_DIR/requirements.txt"

# 4. Run migrations
echo "Running migrations..."
python "$PROJECT_DIR/manage.py" migrate --run-syncdb

# 5. Create superuser if none exists
python "$PROJECT_DIR/manage.py" shell -c "
from apps.core.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin@crane.local', 'admin')
    print('Superuser created: admin@crane.local / admin')
else:
    print('Superuser already exists')
"

# 5.1 Seed ICF demo data after a clean reset
if [ "$CLEAN" -eq 1 ]; then
    echo "Seeding ICF demo data..."
    python "$PROJECT_DIR/manage.py" seed_icf
fi

# 6. Start dev server
echo ""
echo "Starting server at http://localhost:8000"
echo "Admin: http://localhost:8000/admin/"
echo "To rebuild CSS on template changes, run in another terminal:"
echo "  ./bin/tailwindcss -i static/css/crane.src.css -o static/css/crane.css --watch"
echo "Press Ctrl+C to stop"
echo ""
python "$PROJECT_DIR/manage.py" runserver
