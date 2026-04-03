#!/bin/bash
set -e

# Polyglot Devcontainers - Scenario Initialization Script
# This script automates the setup of a standalone scenario for learning purposes.

SCENARIO_NAME="python-secure"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Initializing ${SCENARIO_NAME} scenario..."

# Step 1: Verify we're in the right directory
if [ ! -f "${SCRIPT_DIR}/tasks.py" ]; then
    echo "❌ Error: tasks.py not found. Are you in the scenario directory?"
    exit 1
fi

cd "${SCRIPT_DIR}"

# Step 2: Clean any host artifacts (architecture-specific)
echo "🧹 Cleaning host artifacts..."
rm -rf .venv .artifacts .tmp __pycache__ .pytest_cache .coverage 2>/dev/null || true

# Step 3: Verify bundled dependencies exist
echo "✅ Verifying bundled dependencies..."
if [ ! -f "security-scan-policy.toml" ]; then
    echo "❌ Error: security-scan-policy.toml not found (should be bundled)"
    exit 1
fi

if [ ! -f "scripts/evaluate_python_audit_policy.py" ]; then
    echo "❌ Error: scripts/evaluate_python_audit_policy.py not found (should be bundled)"
    exit 1
fi

# Step 4: Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository (required for pre-commit)..."
    git init
    git add .
    git commit -m "Initialize ${SCENARIO_NAME} scenario" --quiet
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already initialized"
fi

# Step 5: Start DevPod with VSCode
echo "🐳 Starting DevPod container..."
echo "   This will:"
echo "   - Build container (or use cached image)"
echo "   - Install documentation"
echo "   - Create fresh .venv in container"
echo "   - Install all dependencies"
echo "   - Install pre-commit hooks"
echo "   - Open VSCode"
echo ""

if command -v devpod &> /dev/null; then
    devpod up . --ide vscode
    echo ""
    echo "✅ Scenario initialized successfully!"
    echo ""
    echo "📝 Next steps:"
    echo "   1. VSCode should open automatically"
    echo "   2. Open workspace folder: /workspaces/${SCENARIO_NAME}"
    echo "   3. In terminal, navigate: cd /workspaces/${SCENARIO_NAME}"
    echo "   4. Verify setup: task lint && task test"
    echo ""
    echo "🎓 Happy learning!"
else
    echo "❌ Error: devpod command not found"
    echo "   Please install DevPod: https://devpod.sh/docs/getting-started/install"
    exit 1
fi
