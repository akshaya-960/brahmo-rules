from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db import supabase
from pipeline.orchestrator import run_pipeline

app = FastAPI(title="BRAHMO Rules Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/api/users")
def list_users():
    result = supabase.table("users").select("*").execute()
    return result.data

@app.post("/api/pipeline/run")
def run_pipeline_endpoint(user_id: str):
    try:
        return run_pipeline(user_id, supabase)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
