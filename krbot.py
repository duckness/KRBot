import discord
from discord.ext import commands

import os
import sys


def get_prefix(bot_, message):
    prefixes = ['??']
    return commands.when_mentioned_or(*prefixes)(bot_, message)


initial_extensions = ['cogs.announce']

bot = commands.Bot(command_prefix=get_prefix, description='A Discord Bot for King\'s Raid')


@bot.event
async def on_ready():
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    await bot.change_presence(game=discord.Game(name='King\'s Raid'))
    if __name__ == '__main__':
        for extension in initial_extensions:
            try:
                bot.load_extension(extension)
            except Exception as e:
                print(f'Failed to load extension {extension}.', file=sys.stderr)
    print(f'Successfully logged in and booted...!')

bot.run(os.environ['TOKEN'], bot=True, reconnect=True)
