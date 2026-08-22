#!/bin/bash
set -euo pipefail
set +x
# Create the config
rm -f auth.ini
echo "[${EXPERIMENT}]" > auth.ini
if [ -n "${BOT_HANDLE:-}" ]; then
    echo "BOT_HANDLE = @${BOT_HANDLE}" >> auth.ini
fi
if [ -n "${CONSUMER_KEY:-}" ]; then
    echo "CONSUMER_KEY = ${CONSUMER_KEY}" >> auth.ini
fi
if [ -n "${CONSUMER_SECRET:-}" ]; then
    echo "CONSUMER_SECRET = ${CONSUMER_SECRET}" >> auth.ini
fi
if [ -n "${ACCESS_TOKEN:-}" ]; then
    echo "ACCESS_TOKEN = ${ACCESS_TOKEN}" >> auth.ini
fi
if [ -n "${ACCESS_TOKEN_SECRET:-}" ]; then
    echo "ACCESS_TOKEN_SECRET = ${ACCESS_TOKEN_SECRET}" >> auth.ini
fi
if [ -n "${MASTODON_BOT_HANDLE:-}" ]; then
    echo "MASTODON_BOT_HANDLE = ${MASTODON_BOT_HANDLE}" >> auth.ini
fi
if [ -n "${MASTODON_ACCESS_TOKEN:-}" ]; then
    echo "MASTODON_ACCESS_TOKEN = ${MASTODON_ACCESS_TOKEN}" >> auth.ini
fi
if [ -n "${BLUESKY_HANDLE:-}" ]; then
    echo "BLUESKY_HANDLE = ${BLUESKY_HANDLE}" >> auth.ini
fi
if [ -n "${BLUESKY_APP_PASSWORD:-}" ]; then
    echo "BLUESKY_APP_PASSWORD = ${BLUESKY_APP_PASSWORD}" >> auth.ini
fi
# Create the SSH directory and give it the right permissions
mkdir -p ~/.ssh
chmod 700 ~/.ssh
eval "$(ssh-agent -s)"
ssh-add <(printf "%s\n" "$GIT_SSH_PRIV_KEY")
ssh-keyscan -p 7999 gitlab.cern.ch > ~/.ssh/known_hosts
# # Set git user name and email
git config --global user.email "${GITMAIL}"
git config --global user.name "${GITNAME}"
git config --global http.postBuffer 524288000
git config --global https.postBuffer 524288000

echo "auth.ini created for ${EXPERIMENT}"
