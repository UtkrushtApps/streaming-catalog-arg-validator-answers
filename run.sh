#!/usr/bin/env bash
set -uo pipefail

cd /root/task

pip install -q -r requirements.txt

python -m agent --selfcheck
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "selfcheck failed"
  exit "$rc"
fi

echo "ready"

