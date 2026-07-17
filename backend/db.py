import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# All three tables are small and static for the demo session.
# Cache everything in memory at first access so every subsequent
# pipeline run does zero network round-trips to Supabase.
_hierarchy_cache: dict[str, list] = {}
_nodes_cache: dict[str, list] = {}
_users_cache: dict[str, dict] = {}

def get_hierarchy_levels(org_id: str) -> list:
    if org_id not in _hierarchy_cache:
        _hierarchy_cache[org_id] = supabase.table("hierarchy_levels").select("*") \
            .eq("org_id", org_id).execute().data
    return _hierarchy_cache[org_id]

def get_knowledge_nodes(org_id: str) -> list:
    if org_id not in _nodes_cache:
        _nodes_cache[org_id] = supabase.table("knowledge_nodes").select("*") \
            .eq("org_id", org_id).execute().data
    return _nodes_cache[org_id]

def get_user(user_id: str) -> dict | None:
    if user_id not in _users_cache:
        res = supabase.table("users").select("*").eq("id", user_id).execute()
        if res.data:
            _users_cache[user_id] = res.data[0]
    return _users_cache.get(user_id)
