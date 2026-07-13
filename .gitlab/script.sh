#!/bin/bash
set -euo pipefail

git remote set-url origin "${REMOTE_GIT_REPO}"
git fetch origin master
git checkout -B master origin/master

set +e
python cds_paper_bot.py -m 1 -e "${EXPERIMENT}" --arXiv
BOT_EXIT_CODE=$?
set -e

if [[ -n $(git status --short delivery-ledger) ]]; then
    git add delivery-ledger
    git commit -m "update ${EXPERIMENT} delivery ledger"
    git pull --rebase origin master
    git push origin HEAD:master
else
    echo "No delivery-ledger changes found."
fi

exit "${BOT_EXIT_CODE}"
