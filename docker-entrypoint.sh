#!/bin/sh

# create our user and run the bot as that user
USER_ID=${UID:-1234}
GROUP_ID=${GID:-1234}

adduser -S -u $USER_ID -g $GROUP_ID krbot
chown krbot /app
chown krbot /app/*

# run bot as the selfbot user
su-exec krbot "$@"
