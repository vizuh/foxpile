import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import time

# Define the intents for the bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to keep track of channel expiration timestamps and notification status
channel_expirations = {}

async def delete_channel_if_expired(channel_id):
    """Deletes the channel if the current time is past the end_timestamp and sends a notification 12 hours before."""
    while True:
        if channel_id in channel_expirations:
            end_timestamp = channel_expirations[channel_id]['timestamp']
            time_left = end_timestamp - time.time()
            
            if time_left <= 0:
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.delete(reason="Time expired for this channel.")
                del channel_expirations[channel_id]  # Remove the channel from tracking
                break
            elif time_left <= 43200 and not channel_expirations[channel_id].get('notified', False):  # 12 hours in seconds
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send("@here, this channel will expire in less than 12 hours!")
                    channel_expirations[channel_id]['notified'] = True
        await asyncio.sleep(60)  # Sleep for 60 seconds before checking again

@bot.command()
@commands.has_permissions(manage_channels=True)
async def stockpile(ctx, name: str, role_name: str, code: str):
    """Creates a channel that's only accessible by a specified role and includes a stockpile code."""
    if ctx.guild is None:
        await ctx.send("This command can only be used in a server.")
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"The role '{role_name}' does not exist.")
        return

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        role: discord.PermissionOverwrite(read_messages=True)
    }

    channel = await ctx.guild.create_text_channel(name, overwrites=overwrites)
    end_timestamp = time.time() + timedelta(hours=48).total_seconds()
    channel_expirations[channel.id] = {'timestamp': end_timestamp, 'notified': False}

    discord_timestamp = f"<t:{int(end_timestamp)}:F>"
    await channel.send(f"Stockpile Code: {code}. This stockpile expires on {discord_timestamp}.")

    asyncio.create_task(delete_channel_if_expired(channel.id))

@bot.event
async def on_reaction_add(reaction, user):
    """Refreshes the expiration timer every time a new reaction is added to the initial message."""
    channel_id = reaction.message.channel.id
    if user != bot.user and channel_id in channel_expirations:
        new_end_timestamp = time.time() + timedelta(hours=48).total_seconds()
        channel_expirations[channel_id]['timestamp'] = new_end_timestamp
        channel_expirations[channel_id]['notified'] = False  # Reset notification status
        
        discord_timestamp = f"<t:{int(new_end_timestamp)}:F>"
        await reaction.message.channel.send(f"The timer has been refreshed. This stockpile now expires on {discord_timestamp}.")

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot.run('YOUR_BOT_TOKEN')
