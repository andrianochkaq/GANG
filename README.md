# FreeCook

FreeCook is a Ukrainian-language web app for shared refrigerators. It
brings together an AI Chef, shopping lists, calorie and water tracking
and a recipe journal.

## Stack

- Backend: Django 5, Django REST Framework, SimpleJWT, PostgreSQL 16,
  Celery and Redis
- Frontend: React 18, TypeScript, Vite, TanStack Query, Zustand and
  Tailwind
- Infrastructure: Docker Compose, nginx and GitHub Actions

## Repository layout

| Folder      | Contents                                  |
| ----------- | ----------------------------------------- |
| `backend/`  | Django project and its apps               |
| `frontend/` | React + TypeScript app                    |
| `nginx/`    | Reverse proxy configuration               |

The Django skeleton lives in `backend/` and the React skeleton in
`frontend/`. `docker-compose.yml` runs them with their services.

## Getting started

1. Install Git and Docker with Docker Compose.
2. Clone the repository and switch to the `dev` branch:

   ```bash
   git clone https://github.com/andrianochkaq/GANG.git
   cd GANG
   git checkout dev
   ```

3. Create your local environment file and fill in the values:

   ```bash
   cp .env.example .env
   ```

   `.env` is ignored by Git. Every variable the project reads is listed
   in `.env.example`; secrets are left empty there.

4. Start the whole stack:

   ```bash
   docker compose up --build
   ```

   This starts PostgreSQL 16, Redis, Mailpit, the Django API, a Celery
   worker, Celery beat and the Vite dev server. The API container
   enables the `pg_trgm` extension and applies migrations on start.
   Without a `.env` file the stack still starts with development
   defaults.

| Service  | Address                                  |
| -------- | ---------------------------------------- |
| App      | http://localhost:5173                    |
| API      | http://localhost:8000 (`/api/docs/`)     |
| Mailpit  | http://localhost:8025 (all dev emails)   |

Editing a `.py` or `.tsx` file reloads the API and the app. The Celery
worker does not reload by itself: run `docker compose restart celery`
after changing a task. After changing `requirements.txt` or
`package.json`, run `docker compose up --build`. The frontend keeps its
`node_modules` in a volume, so after a `package.json` change also run
`docker compose down` and `docker volume rm freecook_frontend_node_modules`
before starting again. `docker compose down -v` deletes the database
too.

## Backend without Docker

Run PostgreSQL 16 and Redis locally, then from the repository root:

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv/bin/activate elsewhere
pip install -r backend/requirements.txt
cd backend
python manage.py runserver
```

The variables are read from the environment, so export the ones you
need from `.env.example` first. `GET /api/health/` reports the database
and Redis status; the Swagger UI is at `/api/docs/`. Run the tests with
`pytest` from the `backend/` folder; they do not need PostgreSQL or
Redis.

## Frontend without Docker

Install Node.js 20, start the backend as above, then:

```bash
cd frontend
npm install
npm run dev
```

The app opens at http://localhost:5173 and shows the result of
`/api/health/`. It calls the backend at `VITE_API_URL` from the root
`.env` (default in `.env.example`: `http://localhost:8000`). Every UI
string lives in `frontend/src/i18n/uk.json`. Checks: `npm run
typecheck`, `npm test` and `npm run build`.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the branch, commit and
merge rules. Work starts from `dev` and goes back into `dev`; `main` is
used for releases only.
