#!/bin/bash
echo ""
echo "  ================================================"
echo "    AI Coach Companion - One-Click Setup"
echo "  ================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "  [!] Python3 not found. Install it:"
    echo "      brew install python3  (macOS)"
    echo "      sudo apt install python3 python3-pip  (Linux)"
    exit 1
fi

echo "  [1/3] Installing dependencies..."
pip3 install -r requirements.txt -q

echo ""
echo "  [2/3] Creating data directory..."
mkdir -p data

echo ""
echo "  [3/3] Starting AI Coach..."
echo ""
echo "  ================================================"
echo "    App is starting! Opening in your browser..."
echo "    Press Ctrl+C to stop."
echo "  ================================================"
echo ""

streamlit run app.py
