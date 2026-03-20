import os
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

# Config
API_TOKEN   = os.getenv("CLICKUP_API_TOKEN")
LIST_ID     = os.getenv("CLICKUP_LIST_ID")
BASE_URL    = "https://api.clickup.com/api/v2"
HEADERS     = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json"
}

mcp = FastMCP("ClickUpBot")


# ── Helper Functions ──────────────────────────────────────────────────
WORKSPACE_ID = os.getenv("CLICKUP_WORKSPACE_ID")

def get_member_id(name: str) -> int:
    """Look up member ID by name or username."""
    data = clickup_get("/team")
    teams = data.get("teams", [])

    for team in teams:
        for member in team.get("members", []):
            user = member["user"]
            username = (user.get("username") or "").lower()
            email = (user.get("email") or "").lower()

            if name.lower() in username or name.lower() in email:
                return user["id"]

    return None

def clickup_get(path: str, params: dict = None):
    with httpx.Client() as client:
        res = client.get(f"{BASE_URL}{path}", headers=HEADERS, params=params)
        res.raise_for_status()
        return res.json()

def clickup_post(path: str, body: dict):
    with httpx.Client() as client:
        res = client.post(f"{BASE_URL}{path}", headers=HEADERS, json=body)
        res.raise_for_status()
        return res.json()

def clickup_put(path: str, body: dict):
    with httpx.Client() as client:
        res = client.put(f"{BASE_URL}{path}", headers=HEADERS, json=body)
        res.raise_for_status()
        return res.json()


# ── Tool 1: Read Tasks ────────────────────────────────────────────────

@mcp.tool()
def get_tasks(status: str = None, assignee_id: str = None) -> str:
    """Get all tasks from ClickUp. Optionally filter by status or assignee."""

    params = {"include_closed": "false"}
    if status:
        params["statuses[]"] = status
    if assignee_id:
        params["assignees[]"] = assignee_id

    data  = clickup_get(f"/list/{LIST_ID}/task", params=params)
    tasks = data.get("tasks", [])

    if not tasks:
        return "No tasks found."

    lines = []
    for task in tasks:
        name      = task["name"]
        task_id   = task["id"]
        status    = task["status"]["status"].upper()
        priority  = task.get("priority") or {}
        pri       = priority.get("priority", "none")
        assignees = ", ".join(a["username"] for a in task.get("assignees", []))

        lines.append(
            f"[{status}] {name}\n"
            f"  ID: {task_id} | Priority: {pri} | Assignees: {assignees or 'unassigned'}"
        )

    return "\n\n".join(lines)


# ── Tool 2: Create Task ───────────────────────────────────────────────

@mcp.tool()
def create_task(
    name: str,
    description: str = "",
    priority: int = None,
    assignee: str = None,
    due_date: int = None,
) -> str:
    """
    Create a new task in ClickUp.
    Priority: 1=urgent, 2=high, 3=normal, 4=low
    due_date: YYYY-MM-DD format e.g. 2024-12-31
    """

    body = {"name": name}

    if description:
        body["description"] = description
    if priority:
        body["priority"] = priority
    if assignee:
        body["assignees"] = [assignee]
    if due_date:
        from datetime import datetime
        body["due_date"] = int(datetime.fromisoformat(due_date).timestamp() * 1000)
    if assignee:
        user_id = get_member_id(assignee)
        if user_id:
            body["assignees"] = [user_id]
        else:
            return f"Could not find member '{assignee}'. Check the name and try again."


    data = clickup_post(f"/list/{LIST_ID}/task", body)

    return (
        f"Task created successfully.\n"
        f"  Name: {data['name']}\n"
        f"  ID:   {data['id']}\n"
        f"  Status: {data['status']['status']}"
    )


# ── Tool 3: Update Task ───────────────────────────────────────────────

@mcp.tool()
def update_task(
    task_id: str,
    name: str = None,
    status: str = None,
    priority: int = None,
    due_date: str = None,
    assignee: str = None,
) -> str:
    """
    Update an existing task in ClickUp.
    Provide task_id and any fields you want to change.
    Priority: 1=urgent, 2=high, 3=normal, 4=low
    due_date: YYYY-MM-DD format
    """

    body = {}

    if name:
        body["name"] = name
    if status:
        body["status"] = status
    if priority:
        body["priority"] = priority
    if due_date:
        from datetime import datetime
        body["due_date"] = int(datetime.fromisoformat(due_date).timestamp() * 1000)
    if assignee:
        user_id = get_member_id(assignee)
        if user_id:
            body["assignees"] = {"add": [user_id]}  
        else:
            return f"Could not find member '{assignee}'. Check the name and try again."

    if not body:
        return "Nothing to update. Please provide at least one field to change."

    data = clickup_put(f"/task/{task_id}", body)

    return (
        f"Task updated successfully.\n"
        f"  Name:   {data['name']}\n"
        f"  ID:     {data['id']}\n"
        f"  Status: {data['status']['status']}"
        f"  assignees: {', '.join(a['username'] for a in data.get('assignees', [])) or 'unassigned'}"
    )

@mcp.tool()
def list_members() -> str:
    """List all members in the workspace."""
    data = clickup_get("/team")
    teams = data.get("teams", [])

    lines = []
    for team in teams:
        for member in team.get("members", []):
            user = member["user"]
            username = user.get("username") or "no username"
            email = user.get("email") or "no email"
            lines.append(f"{username} (ID: {user['id']} | {email})")

    return "\n".join(lines) if lines else "No members found."
# ── Run ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")