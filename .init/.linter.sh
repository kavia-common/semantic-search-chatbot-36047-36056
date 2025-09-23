#!/bin/bash
cd /home/kavia/workspace/code-generation/semantic-search-chatbot-36047-36056/backend_django
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

