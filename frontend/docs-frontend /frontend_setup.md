# Frontend setup — PsychSync

This document collects **exact, copy-paste ready** steps and file contents for the frontend portion of the PsychSync project. It includes the `frontend/.env` and `frontend/.env.example`, the recommended `src/services/api.ts` example, Husky pre-commit hook content, `lint-staged` suggestion, and verification commands.

> **Save path (suggested):** `frontend/docs/frontend-setup.md`

---

## 1) Files & locations (what to create)

- `frontend/.env.example`  — example environment variables (safe to commit)
- `frontend/.env`          — local environment variables (DO NOT commit)
- `frontend/.gitignore`    — ensure `.env` is ignored (append if necessary)
- `frontend/src/services/api.ts` — small API client (if you don’t have one)
- `frontend/.husky/pre-commit`   — husky hook (executable)
- `frontend/package.json` changes — `prepare` script + optional `lint-staged`


---

## 2) `frontend/.env.example` (copy into `.env` for local development)

```env
# Frontend environment variables (example)
VITE_API_URL=http://localhost:8000/api/v1
# Optional: set the port you want vite to run on
# VITE_PORT=5173
```

**How to create:**

```bash
cat > frontend/.env.example <<'EOF'
VITE_API_URL=http://localhost:8000/api/v1
# VITE_PORT=5173
EOF

# then create a local .env from example (do not commit):
cp frontend/.env.example frontend/.env
```


---

## 3) Ensure `.env` is ignored (append to `frontend/.gitignore`)

Add these lines to `frontend/.gitignore` if they're not already present:

```
# local environment
.env
.env.local
```

**Command to append safely:**

```bash
printf "\n# local environment\n.env\n.env.local\n" >> frontend/.gitignore
```


---

## 4) `src/services/api.ts` (simple, example client)

Place this at `frontend/src/services/api.ts` (adjust types as needed):

```ts
const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1';

export async function apiGet<T = any>(path: string) {
  const res = await fetch(`${API_BASE_URL}${path}`, { credentials: 'include' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}

export async function apiPost<T = any>(path: string, body: unknown) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}

export default { apiGet, apiPost };
```


---

## 5) Install & configure Husky (pre-commit hook)

**From `frontend/` directory:**

```bash
cd frontend
npm install --save-dev husky lint-staged

# add the prepare script (so `npm install` will set up husky automatically)
npm pkg set scripts.prepare="husky install"

# run prepare to create .husky/ and helper files
npm run prepare
```

**Add a pre-commit hook** (recommended path: `frontend/.husky/pre-commit`):

```bash
npx husky add .husky/pre-commit "npm run lint && npm run type-check && npm test"
```

That command creates `.husky/pre-commit` as executable and inserts a small script which runs your npm scripts before a commit.

**(Alternative: create file manually)**

Path: `frontend/.husky/pre-commit`

```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# run linters and tests before commit
npm run lint
npm run type-check
npm test
```

If you create the file manually, make it executable:

```bash
chmod +x frontend/.husky/pre-commit
```


---

## 6) `lint-staged` (optional — runs linters only on staged files)

Add this block to `frontend/package.json` (inside the root object):

```json
"lint-staged": {
  "*.{js,jsx,ts,tsx}": [
    "eslint --fix",
    "prettier --write",
    "git add"
  ]
}
```

Then change the husky pre-commit to run `npx lint-staged` instead of full lint/test:

```bash
npx husky add .husky/pre-commit "npx --no-install lint-staged && npm run type-check"
```


---

## 7) Verification commands (run from `frontend/`)

```bash
# 1) Start dev server
npm run dev

# 2) Build
npm run build

# 3) Lint (fixable issues will be reported)
npm run lint

# 4) Type-check
npm run type-check

# 5) Tests
npm run test
```


---

## 8) Vite warnings you saw — explanation & fixes

### `The project root contains the "#" character` warning

Vite warns if any path segment contains `#` because that can break URL handling in the dev server. It’s safer to remove `#` from any directory name in the path.

**Find current path:**

```bash
pwd
ls -la
```

**Rename the directory** (example — adjust the path to your real case; **quote** paths that contain special characters):

```bash
# example: rename a directory that contains '#'
mv '/Users/sheriftito/Downloads/psychsync/frontend/#' '/Users/sheriftito/Downloads/psychsync/frontend/hash-removed'
```

Or move the whole project to a path without special characters:

```bash
mv '/Users/sheriftito/Downloads/psychsync' '/Users/sheriftito/Projects/psychsync'
```

After renaming/moving, re-run `npm run dev`.


### `Port 5173 is in use, trying another one...`

If another process is using the port, vite will choose the next free port (5174, 5175...). To free the original port:

```bash
# find process on macOS / Linux
lsof -i :5173
# then kill it (replace <PID>)
kill -9 <PID>

# or run vite on a specific port
npm run dev -- --port 5173
```


---

## 9) Troubleshooting & tips

- If `import.meta.env.VITE_API_URL` is `undefined`, confirm the `.env` file is at `frontend/.env` and named exactly `.env` (Vite loads `.env` files from the project root by default).
- If TypeScript complains about `import.meta.env`, ensure `frontend/vite-env.d.ts` contains at least `/// <reference types="vite/client" />`.
- If you use VS Code and see stale TypeScript errors, reload the TS server with `Cmd+Shift+P` → **TypeScript: Restart TS Server**.


---

## 10) Quick checklist (copy/paste)

```bash
# from project root
# 1. create env files
cp frontend/.env.example frontend/.env

# 2. install husky + setup
cd frontend
npm install --save-dev husky lint-staged
npm pkg set scripts.prepare="husky install"
npm run prepare
npx husky add .husky/pre-commit "npm run lint && npm run type-check && npm test"

# 3. verify everything
npm run dev
npm run build
npm run lint
npm run type-check
npm run test
```

---

If you want, I can also generate a ready-to-save `pre-commit` script file and place the exact `frontend/.env.example` contents here in the canvas so you can copy them straight into your repo. (I've included both in this doc — copy & paste where appropriate.)

---

*End of `frontend/docs/frontend-setup.md`*

