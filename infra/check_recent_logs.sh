#!/bin/bash
sudo journalctl -u ontorag-api --no-pager -n 40 | grep -iE "chunk|extract|violation|error|LLM"
