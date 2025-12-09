#!/bin/bash
echo "============================================"
echo "  TTS Timeline Studio"
echo "============================================"
echo

cd "$(dirname "$0")"

# Activate virtual environment if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "Starting server..."
echo
echo "Interface: http://localhost:7860"
echo

python -m uvicorn src.new_ui.app:app --host 0.0.0.0 --port 7860 --reload
