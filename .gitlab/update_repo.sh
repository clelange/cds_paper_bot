#!/bin/bash
set -euo pipefail
set +x
git checkout master
git remote add upstream https://github.com/clelange/cds_paper_bot.git
git fetch upstream
if [[ -n $(git log ..upstream/master) ]]; then
    # Create the SSH directory and give it the right permissions
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
    eval "$(ssh-agent -s)"
    ssh-add <(printf "%s\n" "$GIT_SSH_PRIV_KEY")
    ssh-keyscan -p 7999 gitlab.cern.ch > ~/.ssh/known_hosts
    git config --global user.email "${GITMAIL}"
    git config --global user.name "${GITNAME}"
    git merge upstream/master -m "merge with upstream"
    git remote set-url origin "${REMOTE_GIT_REPO}"
    git push origin HEAD
else
    echo "No changes found."
fi
