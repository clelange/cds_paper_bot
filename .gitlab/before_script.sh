#!/bin/bash
# exit when any command fails
set -e
# echo off
set -x
# Create the config
cat <<EOF > auth.ini
[${EXPERIMENT}]
BOT_HANDLE = @${BOTHANDLE}
CONSUMER_KEY = ${CONSUMER_KEY}
CONSUMER_SECRET = ${CONSUMER_SECRET}
ACCESS_TOKEN = ${ACCESS_TOKEN}
ACCESS_TOKEN_SECRET = ${ACCESS_TOKEN_SECRET}
EOF
# set +x
# # Create the SSH directory and give it the right permissions
# mkdir -p ~/.ssh
# chmod 700 ~/.ssh
# # Adjust SSH config to allow kerberos authentication
# cat .gitlab/ssh_config > ~/.ssh/config
# # Set git user name and email
# set +x
# echo "${SVNPASS}" | kinit "${SVNUSER}@CERN.CH" > /dev/null
set -x
git config --global user.email "${GITMAIL}"
git config --global user.name "${GITNAME}"
git config --global http.postBuffer 524288000
git config --global https.postBuffer 524288000


set +x
echo "auth.ini created for ${EXPERIMENT}"