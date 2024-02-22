##                                                           ##
##    wokring version with buttons for selection of roles    ##
## combined effort of Atroci and Mugna for the common Warden ##
##             ---------------------------------             ##
##                                                           ##

import discord
import asyncio
import time
import os

from discord.ext import commands
from discord.ui import Button, View
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

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
            elif time_left <= 43460 and not channel_expirations[channel_id].get('notified', False):
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send("@here, this channel will expire in about 12 hours!")
                    channel_expirations[channel_id]['notified'] = True
        await asyncio.sleep(60)

def combine_and_split(args):
    combined_string = ' '.join(args)
    separated_args = combined_string.split(',')
    separated_args = filter(None, [arg.strip(', ') for arg in separated_args])
    return list(separated_args)

class CustomView(View):
    def __init__(self, items):
        super().__init__()
        self.selected_item = None  # To store the selected item generically
        for item in items:
            self.add_item(CustomButton(item))

class CustomButton(Button):
    def __init__(self, item):
        label = item.name if hasattr(item, 'name') else str(item)  # Fallback to str if no name attribute
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.item = item

    async def callback(self, interaction):
        self.view.selected_item = self.item  # Set the selected item generically
        for item in self.view.children:
            item.disabled = True
        await interaction.response.edit_message(view=self.view)
        self.view.stop()  # Important to stop the view from waiting


@bot.command()
async def stockpile(ctx, *args):
    await ctx.message.delete()

    end_args = combine_and_split(args)

    if len(end_args) < 2:
        await ctx.send("Please provide at least two arguments: (name,code). extra arguments can be provided if seperated via commas.")
        return

    t_name = end_args[0]
    t_code = end_args[1]
    t_args = end_args[2:]

    if ctx.guild is None:
        await ctx.send("This command can only be used in a server.")
        return

    # Example of using roles, but you can replace this with any kind of items
    items = ctx.author.roles  # Or any list of items you want to use for selection

    view = CustomView(items)
    message = await ctx.send("Select the role that will see this stockpile:", view=view)
    await view.wait()  # Wait for the user to make a selection

    selected_role = view.selected_item

    await message.delete()

    if selected_role is None:
        await ctx.send("No selection made or operation cancelled.")
        return


    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        selected_role: discord.PermissionOverwrite(read_messages=True)
    }

    channel = await ctx.guild.create_text_channel(t_name, overwrites=overwrites)

    end_timestamp = time.time() + timedelta(hours=48).total_seconds()
    channel_expirations[channel.id] = {'timestamp': end_timestamp}

    discord_timestamp = f"<t:{int(end_timestamp)}:F>"
    await channel.send(f"Stockpile Code: {t_code}. This stockpile expires on {discord_timestamp}.")

    for index, arg in enumerate(t_args, start=1):
        await channel.send(f'Extra info {index}: {arg}')

    asyncio.create_task(delete_channel_if_expired(channel.id))

    items = []
    for category in ctx.guild.categories:
        # Check if the author can view any channel in this category
        if any(channel.permissions_for(ctx.author).view_channel for channel in category.channels):
            items.append(category)

    if not items:
        await ctx.send("No visible categories found.")
        return

    view = CustomView(items)
    await channel.send(f"{ctx.author.mention} Select a channel category to move to:", view=view)
    await view.wait()  # Wait for the user to make a selection

    selected_category = view.selected_item

    if selected_category is None:
        await channel.send("No selection made or operation cancelled.")
        return

    if selected_category:
        await channel.edit(category=selected_category)
        await channel.send(f"Channel '{channel.name}' moved to category '{selected_category}'")



@bot.event
async def on_reaction_add(reaction, user):
    if user != bot.user and reaction.message.channel.id in channel_expirations:
        new_end_timestamp = time.time() + timedelta(hours=48).total_seconds()
        channel_expirations[reaction.message.channel.id]['timestamp'] = new_end_timestamp
        channel_expirations[reaction.message.channel.id].pop('notified', None)
        discord_timestamp = f"<t:{int(new_end_timestamp)}:F>"
        await reaction.message.channel.send(
            f"The timer has been refreshed. This stockpile now expires on {discord_timestamp}.")

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot.run(os.getenv('DISCORD_SECRET_KEY'))