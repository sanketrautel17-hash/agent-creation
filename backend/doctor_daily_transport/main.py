from fastapi import FastAPI

app = FastAPI(title="Doctor Daily Transport", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "message": "Transport service placeholder is ready."}
