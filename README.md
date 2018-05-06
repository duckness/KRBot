# KRBot (Discontinued)

A Discord bot for King's Raid. 

## Features

* announces important announcements from [plug.game](https://www.plug.game/kingsraid-en#/) to a channel
* mirrors [MaskOfGoblin](https://maskofgoblin.com) functionality in discord (TBD)

## Setup

~~DM duckness#4861 on discord for the bot link.~~ This bot is no longer in active development, no additional users will be supported. Existing users can continue to use the bot. It is recommended you use [CleoBot](https://discordapp.com/api/oauth2/authorize?client_id=383736694886891520&permissions=85057&scope=bot) instead, it has a lot more features. 

Alternatively, if you wish to run the bot on your own, here are instructions to setup.

### Docker

This is the preferred method to setup, other methods are not supported by me, and probably won't work.

```bash
docker run --name krbot \
    -e UID={user UID on host to use} \
    -e GID={user GID on host to use} \
    -e TOKEN={Discord bot token} \
    -v /path/on/host/to/data:/app/data \
    duckness/krbot
```

## Usage

Command | Description
--- | ---
`??help` | Display a help message with usage instructions.
`??announce <on/off>` | Turn on/off plug.game announcements for the channel, requires `Manage Channel` permissions.
