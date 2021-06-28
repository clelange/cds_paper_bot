#!/bin/bash
# exit when any command fails
set -e
# echo on
set -x
git checkout master
git remote add upstream https://github.com/clelange/cds_paper_bot.git
git fetch upstream
if [[ -n $(git log ..upstream/master) ]]; then
    git config --global user.email "${GITMAIL}"
    git config --global user.name "${GITNAME}"
    git merge upstream/master -m "merge with upstream"
    git remote set-url origin "${REMOTE_GIT_REPO}"
    git push origin HEAD
else
    echo "No changes found."
fi
