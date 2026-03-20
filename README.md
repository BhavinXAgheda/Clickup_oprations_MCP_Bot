# ClickUp MCP Server

A Python-based Model Context Protocol (MCP) server that lets AI agents (like Claude) read, create, and update tasks inside your ClickUp workspace using natural language.

---

## What It Does

This server bridges Claude and ClickUp. Instead of opening ClickUp manually, you can say things like:

- *"Show me all in-progress tasks"*
- *"Create an urgent bug report for the login API timeout, assign it to Bhavin"*
- *"Mark task 86abc as complete"*
- *"Who are the members in my workspace?"*

---

## Project Structure

```
Clickup_Oprations_MCP/
├── clickup_bot.py       # Main MCP server with all tools
├── .env                 # API credentials (never commit this)
├── .env.example         # Template for credentials
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## Prerequisites

- Python 3.10 or higher
- A ClickUp account with API access
- Claude Desktop app installed

---

## Setup

### 1. Clone the project

```bash
git clone https://github.com/your-username/Clickup_Oprations_MCP.git
cd Clickup_Oprations_MCP
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install mcp httpx python-dotenv
```

### 4. Configure your credentials

Create a `.env` file in the project root:

```
CLICKUP_API_TOKEN=pk_your_token_here
CLICKUP_WORKSPACE_ID=90161069568
CLICKUP_LIST_ID=901613649779
```

**How to find each value:**

| Value | Where to find it |
|---|---|
| `CLICKUP_API_TOKEN` | ClickUp Profile → Settings → Apps → Generate Token |
| `CLICKUP_WORKSPACE_ID` | First number in your ClickUp URL: `app.clickup.com/XXXXXXXX/...` |
| `CLICKUP_LIST_ID` | Number after `/li/` in your List URL: `.../li/XXXXXXXXXXXX-1` |

> Your token starts with `pk_`. Keep it secret — never commit it to Git.

---

## Connect to Claude Desktop

Open your Claude Desktop config file:

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

Add the following inside `mcpServers`:

```json
{
  "mcpServers": {
    "ClickUpBot": {
      "command": "/absolute/path/to/Clickup_Oprations_MCP/.venv/bin/python",
      "args": [
        "/absolute/path/to/Clickup_Oprations_MCP/clickup_bot.py"
      ]
    }
  }
}
```

Replace `/absolute/path/to/` with your actual path. You can find it by running `pwd` inside the project folder.

Fully quit and reopen Claude Desktop after saving.

---

## Available Tools

| Tool | What it does | Example prompt |
|---|---|---|
| `get_tasks` | List tasks, optionally filtered | *"Show me all in-progress tasks"* |
| `create_task` | Create a new task | *"Create a high priority task: Fix payment bug"* |
| `update_task` | Update status, priority, name, due date | *"Mark task 86abc as done"* |
| `add_comment` | Add a comment to a task | *"Comment on task 86abc: fix deployed"* |
| `search_tasks` | Search tasks by keyword | *"Find all tasks about authentication"* |
| `list_members` | List all workspace members | *"Who is in my workspace?"* |
| `get_spaces` | List all spaces | *"Show me all spaces"* |
| `get_lists` | List all lists in a space | *"What lists are in the Engineering space?"* |

---

## Priority Levels

| Number | Meaning |
|---|---|
| 1 | Urgent |
| 2 | High |
| 3 | Normal |
| 4 | Low |

---

## Common Statuses

These depend on your ClickUp setup, but typical values are:

- `to do`
- `in progress`
- `review`
- `complete`

---

## Testing Without Claude

You can test each tool directly from the terminal:

```bash
# List all tasks
.venv/bin/python -c "from clickup_bot import get_tasks; print(get_tasks())"

# Filter by status
.venv/bin/python -c "from clickup_bot import get_tasks; print(get_tasks(status='in progress'))"

# Create a task
.venv/bin/python -c "from clickup_bot import create_task; print(create_task('Test task', priority=2))"

# Create and assign by name
.venv/bin/python -c "from clickup_bot import create_task; print(create_task('Fix bug', assignee='Bhavin'))"

# Update a task
.venv/bin/python -c "from clickup_bot import update_task; print(update_task('TASK_ID', status='complete'))"

# List members
.venv/bin/python -c "from clickup_bot import list_members; print(list_members())"
```

---

## Troubleshooting

**Server not connecting to Claude:**
- Make sure you used the absolute path to both Python and the script in the config
- Use `.venv/bin/python` not just `python` so Claude uses the right environment
- Fully quit Claude Desktop (Cmd+Q) and reopen after config changes

**400 Bad Request:**
- Check your List ID — use only the numeric part e.g. `901613649779` not `6-901613649779-1`

**Authorization error:**
- Make sure your token starts with `pk_`
- Check there are no spaces around `=` in your `.env` file

**Member not found when assigning:**
- Run `list_members()` to see exact usernames available
- The search is case-insensitive and matches partial names

**No tasks returned:**
- Verify your `CLICKUP_LIST_ID` is correct
- Check that the list actually has tasks in ClickUp

---

## Security

- Never commit your `.env` file to version control
- Add `.env` to your `.gitignore`
- Rotate your API token from ClickUp settings if it is ever exposed

---

## Dependencies

```
mcp
httpx
python-dotenv
```

Install with:

```bash
pip install mcp httpx python-dotenv
```
