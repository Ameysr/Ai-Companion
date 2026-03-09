"""
squad_client.py — HTTP client for connecting to a Squad host.
Non-host members use this to sync their progress with the host.
"""

import httpx


class SquadClient:
    """HTTP client for syncing with a Squad host."""

    def __init__(self, host_url: str = ""):
        self.host_url = host_url.rstrip("/")
        self._connected = False
        self._squad_id = None
        self._member_name = ""

    @property
    def is_connected(self) -> bool:
        return self._connected and bool(self.host_url)

    def connect(self, host_url: str, invite_code: str, member_name: str) -> dict:
        """Connect to a squad host and join."""
        self.host_url = host_url.rstrip("/")
        self._member_name = member_name

        try:
            # First check squad exists
            resp = httpx.get(
                f"{self.host_url}/api/squad/info/{invite_code}",
                timeout=5.0,
            )
            if resp.status_code != 200:
                return {"error": "Squad not found. Check invite code."}

            squad_info = resp.json()

            # Join the squad
            resp = httpx.post(
                f"{self.host_url}/api/squad/join",
                json={"member_name": member_name, "invite_code": invite_code},
                timeout=5.0,
            )
            if resp.status_code != 200:
                return {"error": "Failed to join squad."}

            join_data = resp.json()
            self._squad_id = join_data["squad_id"]
            self._connected = True

            return {
                "status": "connected",
                "squad_name": join_data["squad_name"],
                "squad_id": self._squad_id,
                "members": squad_info.get("members", []),
            }

        except httpx.ConnectError:
            return {"error": "Cannot reach host. Is the host running?"}
        except Exception as e:
            return {"error": f"Connection failed: {str(e)}"}

    def get_leaderboard(self) -> dict:
        """Fetch leaderboard from host."""
        if not self.is_connected:
            return {"error": "Not connected"}
        try:
            resp = httpx.get(
                f"{self.host_url}/api/squad/{self._squad_id}/leaderboard",
                timeout=5.0,
            )
            return resp.json()
        except Exception:
            return {"error": "Failed to fetch leaderboard"}

    def get_goals(self) -> list:
        """Fetch squad goals from host."""
        if not self.is_connected:
            return []
        try:
            resp = httpx.get(
                f"{self.host_url}/api/squad/{self._squad_id}/goals",
                timeout=5.0,
            )
            return resp.json().get("goals", [])
        except Exception:
            return []

    def update_progress(self, squad_goal_id: int, progress: int) -> bool:
        """Push progress update to host."""
        if not self.is_connected:
            return False
        try:
            resp = httpx.post(
                f"{self.host_url}/api/squad/{self._squad_id}/progress",
                json={
                    "member_name": self._member_name,
                    "squad_goal_id": squad_goal_id,
                    "progress": progress,
                },
                timeout=5.0,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def get_motivation(self) -> dict:
        """Fetch motivation message from host."""
        if not self.is_connected:
            return {"message": "Not connected to squad"}
        try:
            resp = httpx.get(
                f"{self.host_url}/api/squad/{self._squad_id}/motivation",
                params={"member_name": self._member_name},
                timeout=5.0,
            )
            return resp.json()
        except Exception:
            return {"message": "Could not fetch motivation"}

    def create_goal(self, title: str, category: str = "general") -> dict:
        """Create a new squad goal on the host."""
        if not self.is_connected:
            return {"error": "Not connected"}
        try:
            resp = httpx.post(
                f"{self.host_url}/api/squad/{self._squad_id}/goals",
                json={"title": title, "category": category},
                timeout=5.0,
            )
            return resp.json()
        except Exception:
            return {"error": "Failed to create goal"}
