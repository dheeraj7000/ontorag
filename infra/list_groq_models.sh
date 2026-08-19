#!/bin/bash
source /home/ubuntu/ontorag/.env
curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'data' in data:
    for m in sorted(data['data'], key=lambda x: x['id']):
        print(m['id'])
else:
    print(data)
"
