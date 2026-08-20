#!/bin/bash
# Tail recent ontorag-api logs, filtered to the lines that usually matter.
# Usage: ./check_logs.sh [num_lines]   (default 80)
LINES="${1:-80}"
sudo journalctl -u ontorag-api --no-pager -n "$LINES" | grep -iE "violation|extract|chunk|error|fail|LLM"
