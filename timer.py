import discord
from discord.ui import Button, View
from discord.ext import commands, tasks
import asyncio

TOKEN = 'your_bot_token_here'
CHANNEL_ID = 123456789012345678  # The channel ID where notifications are sent

class TimerBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timer_duration = 48 * 3600  # 48 hours in seconds
        self.warning_time = 12 * 3600  # 12 hours in seconds
        self.timer_task = None

    async def setup_hook(self):
        self.timer_task = self.loop.create_task(self.timer_loop())

    async def timer_loop(self):
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)
        while not self.is_closed():
            await asyncio.sleep(self.timer_duration - self.warning_time)
            await channel.send("@everyone Less than 12 hours remaining!")
            await asyncio.sleep(self.warning_time)

    async def reset_timer(self):
        if self.timer_task:
            self.timer_task.cancel()
        self.timer_task = self.loop.create_task(self.timer_loop())

bot = TimerBot(command_prefix='!')

@bot.command(name='reset_timer')
async def reset_timer(ctx):
    await bot.reset_timer()
    await ctx.send("Timer has been reset to 48 hours.")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

bot.run(TOKEN)
