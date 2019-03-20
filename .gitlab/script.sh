#!/bin/bash
# exit when any command fails
set -e
# echo on
set -x
python cds_paper_bot.py --dry -e "${EXPERIMENT}"
if git status --porcelain; then
    git checkout master
    git add ./*_FEED.txt
    git commit -m "update tweeted analyses"
    git remote set-url origin "${REMOTE_GIT_REPO}"
    git remote -v
    ssh -v git@gitlab.cern.ch -p 7999
    git push origin HEAD
else
    echo "No changes found."
fi
