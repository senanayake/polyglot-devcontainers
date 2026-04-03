# Tutorial: Getting Started with Scenarios

**Learning-oriented** | **Hands-on** | **Beginner-friendly**

This tutorial will guide you through using your first polyglot-devcontainers scenario. By the end, you'll have a working Python API development environment and understand the basic workflow.

**Time required:** 15 minutes  
**Prerequisites:** DevPod installed ([installation guide](https://devpod.sh/docs/getting-started/install))

---

## What You'll Learn

- How to obtain and set up a scenario
- How to open a scenario in VSCode
- How to verify your environment is working
- How to make your first code change
- How to run tests and security scans

---

## Step 1: Get the Scenario

First, let's get the `python-api-secure` scenario. This is a production-ready FastAPI template.

### Option A: Clone the Repository

```bash
# Clone the entire repository
git clone https://github.com/senanayake/polyglot-devcontainers.git
cd polyglot-devcontainers/templates/python-api-secure
```

### Option B: Download Just the Scenario

```bash
# Download and extract (future: when scenarios are packaged)
curl -L https://github.com/senanayake/polyglot-devcontainers/archive/main.tar.gz | tar xz
cd polyglot-devcontainers-main/templates/python-api-secure
```

**What you have now:** A complete, self-contained scenario directory with all dependencies bundled.

---

## Step 2: Initialize the Scenario

Run the initialization script:

```bash
./init.sh
```

**What happens:**
1. 🧹 Cleans any host artifacts
2. ✅ Verifies bundled dependencies
3. 📦 Initializes git repository
4. 🐳 Starts DevPod container
5. 🚀 Opens VSCode

**Wait for:** VSCode to open automatically (takes ~30 seconds)

---

## Step 3: Open the Workspace

When VSCode opens:

1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type: `File: Open Folder`
3. Navigate to: `/workspaces/python-api-secure`
4. Click `OK`

**What you see now:** The scenario file structure in the Explorer panel.

---

## Step 4: Navigate to the Workspace

Open a new terminal in VSCode (`Terminal` → `New Terminal`) and navigate:

```bash
cd /workspaces/python-api-secure
pwd
# Should show: /workspaces/python-api-secure
```

**Verify you're in the container:**
```bash
whoami
# Should show: vscode (not your host username)
```

---

## Step 5: Verify the Environment

Check that everything is set up correctly:

```bash
# Check Python version
python3 --version
# Should show: Python 3.12.x

# Check virtual environment exists
ls -la .venv
# Should show: bin/, lib/, include/ directories

# Run the full CI pipeline
task ci
```

**Expected output:**
```
✓ Linting passed
✓ Tests passed
✓ Security scans passed
```

**If you see errors:** See [Troubleshooting](#troubleshooting) below.

---

## Step 6: Start the Development Server

Let's run the API:

```bash
task dev
```

**What you see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Open in browser:** http://localhost:8000/api/docs

**What you see:** Interactive API documentation (Swagger UI)

**Try it:**
1. Click on `GET /api/health`
2. Click `Try it out`
3. Click `Execute`
4. See the response: `{"status": "healthy"}`

**Stop the server:** Press `Ctrl+C` in the terminal

---

## Step 7: Make Your First Change

Let's add a new API endpoint.

### Create a new router file

```bash
# Create the file
cat > src/python_api_secure_template/routers/hello.py << 'EOF'
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def say_hello(name: str = "World"):
    """Say hello to someone."""
    return {"message": f"Hello, {name}!"}
EOF
```

### Register the router

Edit `src/python_api_secure_template/main.py`:

```python
# Add this import at the top
from .routers import hello

# Add this line after the other router registrations
app.include_router(hello.router, prefix="/api/hello", tags=["greetings"])
```

### Test your change

```bash
# Start the server again
task dev
```

**Open in browser:** http://localhost:8000/api/docs

**Try your new endpoint:**
1. Find `GET /api/hello`
2. Click `Try it out`
3. Enter a name (e.g., "Alice")
4. Click `Execute`
5. See: `{"message": "Hello, Alice!"}`

**Congratulations!** You've made your first change to a scenario.

---

## Step 8: Write a Test

Good practice: test your code.

Create `tests/test_hello.py`:

```python
from fastapi.testclient import TestClient
from python_api_secure_template.main import app

client = TestClient(app)

def test_hello_default():
    response = client.get("/api/hello/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}

def test_hello_with_name():
    response = client.get("/api/hello/?name=Alice")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, Alice!"}
```

### Run your tests

```bash
task test
```

**Expected output:**
```
tests/test_hello.py::test_hello_default PASSED
tests/test_hello.py::test_hello_with_name PASSED
```

---

## Step 9: Commit Your Changes

```bash
# Check what changed
git status

# Stage your changes
git add .

# Commit
git commit -m "Add hello endpoint with tests"
```

**What happens:** Pre-commit hooks run automatically:
- Code formatting
- Linting
- Type checking

**If hooks fail:** They'll auto-fix most issues. Just `git add .` and commit again.

---

## What You've Learned

✅ How to initialize a scenario with `./init.sh`  
✅ How to open and navigate the workspace  
✅ How to verify the environment is working  
✅ How to run the development server  
✅ How to add a new API endpoint  
✅ How to write and run tests  
✅ How to commit changes with pre-commit hooks  

---

## Next Steps

Now that you understand the basics:

1. **Explore the codebase** - Look at existing routers, models, and tests
2. **Read the scenario README** - Learn about available tasks and configuration
3. **Try another scenario** - Each teaches different patterns
4. **Build something** - Use the scenario as a starting point for your project

**Recommended next tutorial:** [Building a CRUD API](./building-crud-api.md)

---

## Troubleshooting

### VSCode didn't open automatically

**Solution:**
```bash
# Manually open VSCode
devpod up . --ide vscode
```

### Terminal shows host username, not "vscode"

**Solution:** You're not in the container. Reopen VSCode:
1. Close VSCode
2. Run `devpod up . --ide vscode` again
3. When VSCode opens, use `File → Open Folder → /workspaces/python-api-secure`

### `task ci` fails with formatting errors

**Solution:** Auto-format the code:
```bash
ruff format src tests tasks.py
task ci  # Try again
```

### Port 8000 already in use

**Solution:** Kill the existing process:
```bash
lsof -ti:8000 | xargs kill -9
task dev  # Try again
```

### Import errors when running tests

**Solution:** Reinstall dependencies:
```bash
uv sync --reinstall
task test  # Try again
```

---

## Getting Help

- **Scenario README** - `cat README.md` for scenario-specific help
- **Task list** - `task --list` to see all available commands
- **Man pages** - `man polyglot-python` for runtime guidance
- **GitHub Issues** - Report bugs or ask questions

---

## Summary

You've successfully:
- Set up your first scenario
- Made code changes
- Written tests
- Committed your work

**You're ready to start building!** 🎉
