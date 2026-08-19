#!/bin/bash
sudo journalctl -u ontorag-api --no-pager -n 80 | grep -iE "violation|extract|chunk|error|fail"
