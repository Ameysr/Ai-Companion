"""
squad_server.py — FastAPI sync server for Squad mode.
The host runs this alongside Streamlit. Friends connect via IP.
Only squad goals + progress are shared. Chat/emotions stay private.
"""

import threading
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from storage.database import Database

app = FastAPI(title="AI Coach Squad Sync", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database reference — set by start_server()
_db: Database = None


# ── Models ────────────────────────────────────

class JoinRequest(BaseModel):
    member_name: str
    invite_code: str


class GoalCreate(BaseModel):
    title: str
    category: str = "general"


class ProgressUpdate(BaseModel):
    member_name: str
    squad_goal_id: int
    progress: int


# ── Endpoints ─────────────────────────────────

@app.get("/api/squad/info/{invite_code}")
def get_squad_info(invite_code: str):
    """Get squad info by invite code."""
    squad = _db.get_squad(invite_code=invite_code)
    if not squad:
        raise HTTPException(404, "Squad not found")
    members = _db.get_squad_members(squad["id"])
    return {
        "id": squad["id"],
        "name": squad["name"],
        "invite_code": squad["invite_code"],
        "members": [m["member_name"] for m in members],
        "member_count": len(members),
    }


@app.post("/api/squad/join")
def join_squad(req: JoinRequest):
    """Join a squad by invite code."""
    squad = _db.get_squad(invite_code=req.invite_code)
    if not squad:
        raise HTTPException(404, "Invalid invite code")

    member_id = _db.add_squad_member(squad["id"], req.member_name)

    # Create progress entries for existing goals
    goals = _db.get_squad_goals(squad["id"])
    for g in goals:
        _db.update_squad_goal_progress(g["id"], member_id, 0)

    return {
        "status": "joined",
        "squad_id": squad["id"],
        "squad_name": squad["name"],
        "member_id": member_id,
    }


@app.get("/api/squad/{squad_id}/goals")
def get_goals(squad_id: int):
    """Get all active squad goals."""
    goals = _db.get_squad_goals(squad_id)
    return {"goals": goals}


@app.post("/api/squad/{squad_id}/goals")
def create_goal(squad_id: int, goal: GoalCreate):
    """Create a new squad goal."""
    goal_id = _db.add_squad_goal(squad_id, goal.title, goal.category)
    return {"goal_id": goal_id, "title": goal.title}


@app.post("/api/squad/{squad_id}/progress")
def update_progress(squad_id: int, update: ProgressUpdate):
    """Update a member's progress on a goal."""
    members = _db.get_squad_members(squad_id)
    member = next(
        (m for m in members if m["member_name"].lower() == update.member_name.lower()),
        None
    )
    if not member:
        raise HTTPException(404, "Member not found in squad")

    _db.update_squad_goal_progress(update.squad_goal_id, member["id"], update.progress)
    return {"status": "updated"}


@app.get("/api/squad/{squad_id}/leaderboard")
def get_leaderboard(squad_id: int):
    """Get full leaderboard with all members' progress."""
    summary = _db.get_squad_summary(squad_id)
    return summary


@app.get("/api/squad/{squad_id}/motivation")
def get_motivation(squad_id: int, member_name: str = ""):
    """Get motivation data — who's ahead, who's behind."""
    summary = _db.get_squad_summary(squad_id)
    rankings = summary.get("rankings", [])

    if not rankings or not member_name:
        return {"message": "No data yet. Start completing goals!"}

    my_rank = next((r for r in rankings if r["name"].lower() == member_name.lower()), None)
    leader = rankings[0] if rankings else None

    if not my_rank:
        return {"message": "Start updating your progress to see where you stand!"}

    if leader and leader["name"].lower() != member_name.lower():
        gap = leader["avg_progress"] - my_rank["avg_progress"]
        if gap > 20:
            return {
                "message": f"{leader['name']} is at {leader['avg_progress']}% avg. You're at {my_rank['avg_progress']}%. Close the gap!",
                "leader": leader["name"],
                "gap": round(gap, 1),
            }
        elif gap > 0:
            return {
                "message": f"You're close to {leader['name']}! Just {round(gap)}% behind. One push and you're there!",
                "leader": leader["name"],
                "gap": round(gap, 1),
            }
    elif leader and leader["name"].lower() == member_name.lower():
        return {
            "message": "You're leading the squad! Keep the momentum going.",
            "leader": member_name,
            "gap": 0,
        }

    return {"message": "Keep pushing!"}


# ── Server Control ────────────────────────────

_server_thread = None
_server_instance = None


def start_server(db: Database, port: int = 8502):
    """Start the FastAPI sync server in a background thread."""
    global _db, _server_thread, _server_instance
    _db = db

    if _server_thread and _server_thread.is_alive():
        return port  # Already running

    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    _server_instance = uvicorn.Server(config)

    _server_thread = threading.Thread(target=_server_instance.run, daemon=True)
    _server_thread.start()
    return port


def is_running() -> bool:
    return _server_thread is not None and _server_thread.is_alive()
