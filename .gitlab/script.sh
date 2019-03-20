#!/bin/bash
# exit when any command fails
set -e
# echo on
set -x
python cds_paper_bot.py --dry -e "${EXPERIMENT}"
if git status --porcelain; then
    git add ./*_FEED.txt
    git commit -m "update tweeted analyses"
    git remote add kerberos "${REMOTE_GIT_REPO}"
    git push kerberos HEAD
else
    echo "No changes found."
fi
