# How-To: Use Scenarios Standalone

**Task-oriented** | **Problem-solving** | **Step-by-step**

This guide shows you how to use polyglot-devcontainers scenarios as standalone learning environments or project starters, independent of the main repository.

---

## Prerequisites

- DevPod installed ([installation guide](https://devpod.sh/docs/getting-started/install))
- Git installed
- Basic command-line familiarity

---

## Quick Method: Using init.sh

The fastest way to set up a standalone scenario.

### Step 1: Copy the Scenario

```bash
# Copy from cloned repository
cp -r /path/to/polyglot-devcontainers/templates/python-api-secure ~/my-projects/

# Or download directly (when packaged)
cd ~/my-projects
curl -L https://github.com/senanayake/polyglot-devcontainers/archive/main.tar.gz | tar xz
mv polyglot-devcontainers-main/templates/python-api-secure .
```

### Step 2: Run the Initialization Script

```bash
cd ~/my-projects/python-api-secure
./init.sh
```

**What the script does:**
- Cleans architecture-specific artifacts (.venv, __pycache__)
- Verifies bundled dependencies exist
- Initializes git repository
- Starts DevPod with VSCode

**Result:** Working development environment in < 5 minutes.

---

## Manual Method: Step-by-Step Control

If you prefer manual control or want to understand each step.

### Step 1: Copy the Scenario

```bash
cp -r /path/to/polyglot-devcontainers/templates/python-api-secure ~/my-projects/
cd ~/my-projects/python-api-secure
```

### Step 2: Clean Host Artifacts

Remove any architecture-specific files that may have been copied:

```bash
rm -rf .venv .artifacts .tmp __pycache__ .pytest_cache .coverage
```

**Why:** These files are architecture-specific (macOS vs Linux) and will cause errors in the container.

### Step 3: Verify Dependencies

Check that required files are bundled:

```bash
ls security-scan-policy.toml
ls scripts/evaluate_python_audit_policy.py
```

**If missing:** The scenario may not be self-contained. Copy from main repo:
```bash
cp /path/to/polyglot-devcontainers/security-scan-policy.toml .
cp /path/to/polyglot-devcontainers/scripts/evaluate_python_audit_policy.py scripts/
```

### Step 4: Initialize Git Repository

```bash
git init
git add .
git commit -m "Initialize scenario"
```

**Why:** Pre-commit hooks require a git repository to function.

### Step 5: Start DevPod

```bash
devpod up . --ide vscode
```

**Wait for:** Container to build and VSCode to open (~1-2 minutes first time, ~30 seconds after).

### Step 6: Open Workspace

In VSCode:
1. `Cmd+Shift+P` → `File: Open Folder`
2. Navigate to `/workspaces/python-api-secure`
3. Click `OK`

### Step 7: Verify Setup

```bash
cd /workspaces/python-api-secure
task ci
```

**Expected:** All checks pass.

---

## Customizing for Your Project

Once you have the scenario running, customize it for your needs.

### Rename the Project

```bash
# Update pyproject.toml
sed -i '' 's/python-api-secure-template/my-project-name/g' pyproject.toml

# Rename the package directory
mv src/python_api_secure_template src/my_project_name

# Update imports in code
find src tests -type f -name "*.py" -exec sed -i '' 's/python_api_secure_template/my_project_name/g' {} +

# Reinstall
uv sync
```

### Update Configuration

Edit `src/my_project_name/config.py`:

```python
class Settings(BaseSettings):
    PROJECT_NAME: str = "My Project"
    DATABASE_URL: str = "postgresql://user:pass@localhost/mydb"
    SECRET_KEY: str = "change-me-in-production"
    # Add your settings
```

### Remove Example Code

```bash
# Remove example routers
rm src/my_project_name/routers/items.py

# Remove example tests
rm tests/test_api.py

# Update main.py to remove example router registration
```

---

## Sharing Your Scenario

If you want to share your customized scenario with others.

### Option 1: Git Repository

```bash
# Create a new repository
git remote add origin https://github.com/yourusername/my-project.git
git push -u origin main
```

**Others can use it:**
```bash
git clone https://github.com/yourusername/my-project.git
cd my-project
./init.sh
```

### Option 2: Archive

```bash
# Create a distributable archive
tar -czf my-scenario.tar.gz \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='.artifacts' \
  .

# Share the archive
# Others extract and run: ./init.sh
```

---

## Troubleshooting

### "Exec format error" when starting container

**Cause:** Architecture-specific .venv copied from host to container.

**Solution:**
```bash
rm -rf .venv
devpod delete <workspace-name>
devpod up .
```

### "StopIteration" error in tasks.py

**Cause:** Missing REPO_ROOT fallback (older template version).

**Solution:** Update to latest template or add fallback:
```python
try:
    REPO_ROOT = next(
        parent for parent in Path(__file__).resolve().parents 
        if (parent / "AGENTS.md").exists()
    )
except StopIteration:
    REPO_ROOT = ROOT  # Fallback to template directory
```

### "git failed" error during pre-commit install

**Cause:** Git repository not initialized.

**Solution:**
```bash
git init
git add .
git commit -m "Initial commit"
devpod delete <workspace-name>
devpod up .
```

### VSCode opens but shows empty file explorer

**Cause:** Workspace folder not opened.

**Solution:**
1. `File` → `Open Folder`
2. Navigate to `/workspaces/<scenario-name>`
3. Click `OK`

---

## Best Practices

### Do's

✅ **Always run init.sh** - Automates all setup steps correctly  
✅ **Commit early** - Initialize git before starting work  
✅ **Use .gitignore** - Scenarios include proper .gitignore files  
✅ **Keep dependencies bundled** - Don't remove security-scan-policy.toml or scripts/  
✅ **Test in container** - Run `task ci` to verify everything works  

### Don'ts

❌ **Don't copy .venv** - Always exclude architecture-specific artifacts  
❌ **Don't skip git init** - Pre-commit requires git context  
❌ **Don't modify bundled files** - Keep security-scan-policy.toml and scripts/ as-is  
❌ **Don't test on host** - Always test inside the container  
❌ **Don't commit secrets** - Use .env files (already gitignored)  

---

## Related Guides

- [Getting Started Tutorial](../tutorials/getting-started.md) - First-time scenario usage
- [Scenario Architecture](../explanation/scenario-architecture.md) - How scenarios work
- [Scenario Reference](../reference/scenario-structure.md) - Complete scenario structure
- [Troubleshooting Guide](./troubleshooting.md) - Common issues and solutions
