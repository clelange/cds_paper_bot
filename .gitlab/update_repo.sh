#!/bin/bash
set -euo pipefail
set +x
git fetch origin master
git checkout -B master origin/master
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
    # The push pipeline builds the commit that was just synchronized. Building in
    # this web pipeline would use its older, immutable CI_COMMIT_SHA checkout.
    git push -o ci.variable="BUILD_IMAGE=true" origin HEAD:master
else
    echo "No changes found."
fi
