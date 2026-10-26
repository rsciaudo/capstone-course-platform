# Status
Currently this code demonstrates a shell of the frontend of the most basic, foundational functionality of the admin interface to get a feel for how things should be connected. I am using react javascript and vite to run locally in my browser.

# Local stack

Copy `.env.example` to `.env`, then start the database, backend, and frontend:

```bash
docker compose up --build
```

Apply the schema once the database is healthy:

```bash
bash db/apply.sh
```

Open the admin UI at http://localhost:5173. Check the backend at http://localhost:8000/api/health.

# Sources
I have been using Cursor to assist with generating the code. I give instructions one task at a time, review the plan for implementation, build the plan and review changed files. Then, I can make manual adjustments where needed. 
