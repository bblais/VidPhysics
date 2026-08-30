#!/usr/bin/env bash
cd "$(dirname "$0")"
pwd
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install
uv venv --clear
