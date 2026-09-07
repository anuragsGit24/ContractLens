# ContractLens React frontend

This frontend uses the existing ContractLens FastAPI service. It does not connect to Qdrant directly: uploads and analysis requests go through the backend at `/v1`.

## Run with the existing services

From the repository root, install the frontend dependencies once:

```powershell
Push-Location frontend_1
npm install
Pop-Location
```

Then run `start_contractlens.ps1`. It starts:

- FastAPI backend at `http://127.0.0.1:8000`
- Original Streamlit frontend at `http://127.0.0.1:8501`
- This React frontend at `http://127.0.0.1:5173`

Vite proxies `/v1` to the existing backend, so no second backend or local vector database is created. To use another backend during development, set `VITE_API_BASE_URL` to its `/v1` base URL and ensure that deployment permits browser requests to it.

## Useful commands

```powershell
npm run dev
npm run build
npm run lint
```
