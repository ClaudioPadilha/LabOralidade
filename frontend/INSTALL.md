# Frontend setup

This repository deliberately does not include `node_modules` to keep the repo small.

To install the frontend dependencies locally, run:

```bash
# Ensure you have Node.js (LTS) and npm installed (use nvm if needed)
cd frontend
npm install
```

If you want to start the dev server:

```bash
npm run dev
# Open http://localhost:5173
```

If you previously had `node_modules` committed, remove them locally and ensure `.gitignore` contains `frontend/node_modules/` so they are not added again.
