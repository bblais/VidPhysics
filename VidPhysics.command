#!/bin/bash
cd "$(dirname "$0")"

# Ensure common install directories (like ~/.local/bin) are in PATH
export PATH="$HOME/.local/bin:$PATH"

# Check if uv is installed; if not, run the installation steps
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Reload PATH to include newly installed uv
    export PATH="$HOME/.local/bin:$PATH"
    
    uv python install
    uv venv --clear
fi

# Run the python script using uv
uv run "VidPhysics.py"

