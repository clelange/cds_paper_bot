#!/bin/bash
# exit when any command fails
set -e
# echo on
set -x
git checkout master
git remote add upstream https://github.com/clelange/cds_paper_bot.git
git fetch upstream
if [[ -n $(git log ..upstream/master) ]]; then
    # Create the SSH directory and give it the right permissions
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
    eval "$(ssh-agent -s)"
    set -x
    ssh-add <(echo "$GIT_SSH_PRIV_KEY")
    echo "$GIT_SSH_PRIV_KEY" > ~/.ssh/id_rsa
    set +x
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan -p 7999 gitlab.cern.ch > ~/.ssh/known_hosts
    set -x
    git config --global user.email "${GITMAIL}"
    git config --global user.name "${GITNAME}"
    set +x
    git merge upstream/master -m "merge with upstream"
    git remote set-url origin "${REMOTE_GIT_REPO}"
    git push origin HEAD
else
    echo "No changes found."
fi
