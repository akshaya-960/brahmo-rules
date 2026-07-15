from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db import supabase

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
def run_pipeline(user_id: str):
    raise HTTPException(status_code=501, detail="Pipeline not implemented yet")

# trigger ci
