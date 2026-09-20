# Smart Mail Manager desktop UI

The Electron/React interface uses the existing Python Gmail, SQLite, FAISS,
and RAG backend through a small local FastAPI adapter. It does not duplicate
email storage or AI retrieval in the browser.

## Start locally

Install the Python dependencies (from the project root):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-api.txt
```

Install the desktop dependencies:

```powershell
npm install
```

In terminal 1, run the backend from `src` so its existing imports resolve:

```powershell
cd src
..\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

In terminal 2, run the Vite server, then launch Electron in a third terminal:

```powershell
npm run dev
$env:VITE_DEV_SERVER_URL = 'http://localhost:5173'
npm run desktop
```

`npm run build` validates a production UI bundle. The development shell expects
Vite at `http://localhost:5173`; when it is unavailable Electron falls back to
the built `dist` bundle.

## Manual check

1. Start the API and ensure `http://127.0.0.1:8000/api/health` returns `ok`.
2. Open the desktop app and switch Inbox, Starred, Important, Attachments, and a category.
3. Open an email and verify its headers, category, attachment indicator, and body.
4. Ask “Show my latest emails” and open a returned source card.
5. Click Sync and confirm the success/error message is user-friendly.
