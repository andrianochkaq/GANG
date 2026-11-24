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

The folders are created empty. The Django skeleton, the React skeleton
and the Docker Compose setup are added by the next Sprint 0 tickets
(FC-002, FC-003 and FC-004).

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
   docker compose up
   ```

   This command works once FC-004 is merged. It starts the Django API,
   the React app, PostgreSQL, Redis and Celery.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the branch, commit and
merge rules. Work starts from `dev` and goes back into `dev`; `main` is
used for releases only.
