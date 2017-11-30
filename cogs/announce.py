import aiohttp
import asyncio
import async_timeout
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
import parsedatetime
import pytz
from tzlocal import get_localzone

from datetime import datetime
import html
import logging
import json
import re


def is_dm_or_manage_channel():
    async def predicate(ctx):
        msg = ctx.message
        ch = msg.channel
        permissions = ch.permissions_for(msg.author)
        return permissions.manage_channels and ctx.guild is not None
    return commands.check(predicate)


class AnnounceCog:

    URLS = ['https://www.plug.game/kingsraid-en/posts?menuId=1',   # Notices
            'https://www.plug.game/kingsraid-en/posts?menuId=2',   # Events
            'https://www.plug.game/kingsraid-en/posts?menuId=9',   # Patch Note
            'https://www.plug.game/kingsraid-en/posts?menuId=12']  # Green Note

    def __init__(self, bot):
        self.bot = bot
        self.bg_task = bot.loop.create_task(self.announcement())
        self.channel_path = '/app/data/channels.json'
        self.latest = {}
        try:
            with open(self.channel_path) as json_data:
                self.channels = json.load(json_data)
        except FileNotFoundError:
            open(self.channel_path, 'a').close()
            self.channels = {}
        except Exception as e:
            raise(e)

    # The announce command
    @commands.group()
    async def announce(self, ctx):
        """Turn on/off plug.game announcements for this channel"""
        if ctx.invoked_subcommand is None:
            await ctx.send(f'Invalid command.')

    @announce.command(name='on')
    @is_dm_or_manage_channel()
    async def announce_on(self, ctx):
        """turn on announcements"""
        cid = str(ctx.channel.id)
        self.channels[cid] = True
        await ctx.send(f'Announcements have been turned on for this channel.')
        self.write_channels()

    @announce.command(name='off')
    @is_dm_or_manage_channel()
    async def announce_off(self, ctx):
        """turn off announcements"""
        cid = str(ctx.channel.id)
        self.channels[cid] = False
        await ctx.send(f'Announcements have been turned off for this channel.')
        self.write_channels()

    @announce.command(name='latest')
    async def announce_latest(self, ctx):
        """outputs the latest announcement"""
        await ctx.send(embed=self.get_embed(self.latest))

    # Grab pages from Plug every minute and parse them for updates and send the updates to registered channels
    async def announcement(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            client = aiohttp.ClientSession(loop=self.bot.loop)
            async with client as session:
                pages = await asyncio.gather(
                    *[self.fetch(session, url) for url in self.URLS],
                    loop=self.bot.loop,
                    return_exceptions=True
                )
            await self.send_new_posts(pages)
            await asyncio.sleep(60)

    async def fetch(self, session, url):
        async with async_timeout.timeout(10):
            async with session.get(url) as response:
                return await response.text()

    # Posts the page on discord if necessary
    async def send_new_posts(self, pages):
        logging.info('Checking for new posts')
        result = self.process_pages(pages)
        ids = result[0]
        attributes = result[1]
        self.latest = attributes[str(ids[-1])]
        path = '/app/data/posts.txt'
        try:
            with open(path, 'r+') as f:
                arr = f.readlines()
                num_arr = [int(s.rstrip()) for s in arr]
                for id_ in ids:
                    if id_ not in num_arr:
                        logging.info('New post found ' + str(id_))
                        f.write(str(id_) + '\n')
                        embed = self.get_embed(attributes[str(id_)])
                        for key in self.channels:
                            if self.channels[key]:
                                chan = self.bot.get_channel(int(key))
                                # be extra sure we can post
                                if isinstance(chan, discord.abc.GuildChannel):
                                    await chan.send(embed=embed)
                                else:
                                    logging.warning(key + " is invalid, removing")
                                    self.channels[key] = False
                                    self.write_channels()
        except FileNotFoundError:  # don't flood the channel on first run, instead, just get a list of posts
            with open(path, 'a') as f:
                for id_ in ids:
                    f.write(str(id_) + '\n')
        except Exception as e:
            raise(e)

    def get_embed(self, dic):
        if dic:
            embed = discord.Embed(title=dic['title'],
                                  description=dic['description'],
                                  url=dic['url'],
                                  timestamp=dic['timestamp'])
            embed.set_author(name=dic['author']['name'],
                             url=dic['author']['url'],
                             icon_url=dic['author']['icon_url'])
            embed.set_thumbnail(url=dic['thumbnail']['url'])
            return embed
        else:
            return discord.Embed(title='No Articles')

    def process_pages(self, pages):
        ids = []
        attributes = {}
        for i, page in enumerate(pages):
            soup = BeautifulSoup(page, 'html.parser')
            contents = soup.find_all(class_='frame_plug')
            # get a list of article-ids
            ids += [int(content.attrs['data-articleid']) for content in contents]
            # get a dictionary of attributes of every forum post in the page
            attributes.update({
                content.attrs['data-articleid']: {
                    'title': re.sub('\s+', ' ', html.unescape(content.find(class_='tit_feed').string)).strip(),
                    'description': re.sub('\s+', ' ', html.unescape(content.find(class_='txt_feed').string)).strip(),
                    'url': 'https://www.plug.game/kingsraid-en/posts/' + content.attrs['data-articleid'],
                    'thumbnail': {'url': content.find(class_='img').attrs['style'][21:-1]},
                    'timestamp': self.get_time(content.find_all(class_='time')[1].string),
                    'author': {
                        'name': re.sub('\s+', ' ', content.find(class_='name').string).strip(),
                        'url': 'https://plug.game' + content.find(class_='name').attrs['href'],
                        'icon_url': content.find(class_='thumb').attrs['src']
                    }
                }
                for content in contents
            })
        ids.sort()
        return ids, attributes

    def get_time(self, time_str):
        # parsedatetime NLP does not understand min/hr
        time_str = time_str.replace('min', 'minute').replace('hr', 'hour')
        cal = parsedatetime.Calendar()
        # I honestly don't care if it can't parse the time correctly, it will just output current time
        dt = datetime(*cal.parse(time_str)[0][:6])
        return dt.replace(tzinfo=get_localzone()).astimezone(tz=pytz.utc)

    def write_channels(self):
        with open(self.channel_path, 'w') as json_data:
            json_data.write(json.dumps(self.channels))


def setup(bot):
    bot.add_cog(AnnounceCog(bot))
