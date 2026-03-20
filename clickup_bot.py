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
    description: str = None,
) -> str:
    """
    Update an existing task in ClickUp.
    Provide task_id and any fields you want to change.
    Priority: 1=urgent, 2=high, 3=normal, 4=low
    due_date: YYYY-MM-DD format
    description: set to empty string "" to clear description
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
    if description:  # allow clearing description with empty string
        body["description"] = description
    if not body:
        return "Nothing to update. Please provide at least one field to change."

    data = clickup_put(f"/task/{task_id}", body)

    return (
        f"Task updated successfully.\n"
        f"  Name:   {data['name']}\n"
        f"  ID:     {data['id']}\n"
        f"  Status: {data['status']['status']}"
        f"  assignees: {', '.join(a['username'] for a in data.get('assignees', [])) or 'unassigned'}"
        f"  description: {data.get('description', 'No description')}"
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

@mcp.tool()
def get_task_details(task_id: str) -> str:
    """Get full details of a specific task by its ID."""

    data = clickup_get(f"/task/{task_id}")

    # basic fields
    name        = data.get("name", "N/A")
    status      = data["status"]["status"].upper()
    priority    = (data.get("priority") or {}).get("priority", "none")
    description = data.get("description", "No description")
    assignees   = ", ".join(a["username"] for a in data.get("assignees", [])) or "unassigned"

    # due date
    due_ts = data.get("due_date")
    if due_ts:
        from datetime import datetime
        due_date = datetime.fromtimestamp(int(due_ts) / 1000).strftime("%Y-%m-%d")
    else:
        due_date = "not set"

    # subtasks and comments count
    subtasks = data.get("subtasks", [])
    subtask_lines = "\n".join(
        f"  - [{s['status']['status'].upper()}] {s['name']} (ID: {s['id']})"
        for s in subtasks
    ) or "  none"

    return (
        f"Name        : {name}\n"
        f"ID          : {task_id}\n"
        f"Status      : {status}\n"
        f"Priority    : {priority}\n"
        f"Assignees   : {assignees}\n"
        f"Due Date    : {due_date}\n"
        f"Description : {description}\n"
        f"Subtasks    :\n{subtask_lines}"
    )

def clickup_delete(path: str):
    with httpx.Client() as client:
        res = client.delete(f"{BASE_URL}{path}", headers=HEADERS)
        res.raise_for_status()
        return True


@mcp.tool()
def delete_task(task_id: str) -> str:
    """Permanently delete a task by its ID."""

    # fetch name first so confirmation is meaningful
    data = clickup_get(f"/task/{task_id}")
    task_name = data.get("name", "Unknown")

    clickup_delete(f"/task/{task_id}")

    return (
        f"Task deleted successfully.\n"
        f"  Name : {task_name}\n"
        f"  ID   : {task_id}"
    )

@mcp.tool()
def create_subtask(
    parent_task_id: str,
    name: str,
    description: str = "",
    assignee: str = None,
    priority: int = None,
) -> str:
    """
    Create a subtask under an existing task.
    assignee: person's name or username e.g. 'Bhavin'
    priority: 1=urgent, 2=high, 3=normal, 4=low
    """

    body = {
        "name": name,
        "parent": parent_task_id
    }

    if description:
        body["description"] = description
    if priority:
        body["priority"] = priority
    if assignee:
        user_id = get_member_id(assignee)
        if user_id:
            body["assignees"] = [user_id]
        else:
            return f"Could not find member '{assignee}'. Check the name and try again."

    data = clickup_post(f"/list/{LIST_ID}/task", body)

    return (
        f"Subtask created successfully.\n"
        f"  Name      : {data['name']}\n"
        f"  ID        : {data['id']}\n"
        f"  Parent ID : {parent_task_id}\n"
        f"  Status    : {data['status']['status']}"
    )
# ── Run ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")