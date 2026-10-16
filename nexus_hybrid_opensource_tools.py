"""NEXUS open-source management tools. No simulated release or notification counts."""
import asyncio
from nexus_release_adapters import AdapterError, release_preview, notifications
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class OpenSourceToolsEngine:
    def __init__(self, db=None):
        self.db = db
        self.tools_collection = db.opensource_tools if db is not None else None
        self.tools = [
            {"name": "semantic-release", "status": "not_configured"},
            {"name": "octobox", "status": "not_configured"},
        ]

    async def list_tools(self, category: str = "all") -> Dict:
        return {"success": True, "tools": self.tools,
                "total": len(self.tools), "category": category}

    async def automate_release(self, repo: str) -> Dict:
        if not isinstance(repo, str) or not repo.strip():
            return {"success": False, "error": "repository_required"}
        try:
            return await asyncio.to_thread(release_preview, repo)
        except AdapterError as exc:
            return {"success": False, "error": str(exc), "version_released": None,
                    "changelog_generated": False}

    async def manage_notifications(self, user_id: str) -> Dict:
        if not isinstance(user_id, str) or not user_id.strip():
            return {"success": False, "error": "user_id_required"}
        try:
            return await asyncio.to_thread(notifications, user_id)
        except AdapterError as exc:
            return {"success": False, "error": str(exc), "unread_count": None,
                    "filtered_count": None}

    def get_capabilities(self) -> Dict:
        return {"name": "Open Source Tools Hybrid", "version": "1.0.1",
                "tools_count": len(self.tools),
                "integrations": {"semantic-release": "not_configured", "octobox": "not_configured"}}


hybrid_opensource_tools = OpenSourceToolsEngine(db=None)


def create_opensource_tools_engine(db):
    global hybrid_opensource_tools
    hybrid_opensource_tools = OpenSourceToolsEngine(db)
    return hybrid_opensource_tools
