##                                                           ##
##                          VANILLA                          ##
## combined effort of Atroci and Mugna for the common Warden ##
##      Credits to - Andre Rodrigues - AKA  AndreLuizSr      ##
##               NEEDS A BOT TOKEN TO FUNCTION               ##
##            This is a working version 04/03/2024           ##



import discord
from discord.ext import commands
from discord.ui import Button, View
import aiohttp
import asyncio
import datetime
from datetime import timedelta
import time
import os
from ui_elements import CustomView, PaginatedButtonsView
from string_utils import combine_and_split
from imger import extract_text_with_conditions
from fxhl_api_utils import fetch_n_save, region_storages, controlled_regions
from data_management import save_to_json, load_from_json

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.message_content = True

warden_collies = ['WARDENS', 'COLONIALS']
yes_or_no = ['Yes', 'No']
fxpl = 'fxpl'

bot = commands.Bot(command_prefix='!', intents=intents)

file_path = 'FILE_PATH'

fxpl_values = {}
fxpl_file_name = 'fxpl.json'

sides_values = {}
sides_file_name = 'sides.json'

channel_expirations = {}
channels_file_name = 'channels.json'


async def delete_channel_if_expired():
    """
    Checks for expired channels and deletes them. Also sends notifications before the expiration.
    """
    global channel_expirations
    while True:
        print(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), 'Running expirations.')
        temp_count = 0
        for channel_id in list(channel_expirations.keys()):
            temp_count += 1
            end_timestamp = channel_expirations[channel_id]['timestamp']
            time_left = end_timestamp - time.time()

            if time_left <= 0:
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.delete(reason="Time expired for this channel.")
                del channel_expirations[channel_id]
                break
            else:
                try:
                    if time_left <= 18000 and not channel_expirations[channel_id]['final notice'] == 'True':
                        channel = bot.get_channel(channel_id)
                        if channel:
                            await channel.send("@everyone, this channel will expire in about 5 hours!")
                            channel_expirations[channel_id]['final notice'] = 'True'
                    elif time_left <= 43200 and not channel_expirations[channel_id]['notified'] == 'True':
                        channel = bot.get_channel(channel_id)
                        if channel:
                            await channel.send("@here, this channel will expire in about 12 hours!")
                            channel_expirations[channel_id]['notified'] = 'True'
                except KeyError:
                    continue
        print(f"Expiry iterations over, overall {temp_count} channels checked")
        await asyncio.sleep(300)


async def delete_after_delay(msg, delay):
    """
    Deletes a given message after a specified delay.

    Args:
    - msg: The message to delete.
    - delay: The delay in seconds before the message is deleted.
    """
    await asyncio.sleep(delay)
    await msg.delete()


async def create_stockpile_channel(ctx, t_name, t_code, t_args):
    """
    Creates a stockpile channel with specific settings and sends initial messages.

    Args:
    - ctx: The context of the command.
    - t_name: The name of the stockpile.
    - t_code: The code of the stockpile.
    - t_args: Additional arguments or information about the stockpile.
    """
    global channel_expirations
    if ctx.guild is None:
        t_msg = await ctx.send("This command can only be used in a server.")
        asyncio.create_task(delete_after_delay(t_msg, 10))
        return

    items = ctx.author.roles
    view = CustomView(items)
    r_message = await ctx.send("Select the role that will see this stockpile:", view=view)
    await view.wait()

    selected_role = view.selected_item
    await r_message.delete()

    if selected_role is None:
        t_msg = await ctx.send("No selection made or operation cancelled.")
        asyncio.create_task(delete_after_delay(t_msg, 10))
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

    items = []
    for category in ctx.guild.categories:
        if any(channel.permissions_for(ctx.author).view_channel for channel in category.channels):
            items.append(category)

    if not items:
        t_msg = await ctx.send("No visible categories found.")
        asyncio.create_task(delete_after_delay(t_msg, 10))
        return

    view = CustomView(items)
    cat_msg = await channel.send(f"{ctx.author.mention} Select a channel category to move to:", view=view)
    await view.wait()

    selected_category = view.selected_item
    await cat_msg.delete()

    if selected_category is None:
        t_msg = await channel.send("No selection made or operation cancelled.")
        asyncio.create_task(delete_after_delay(t_msg, 10))
        return

    if selected_category:
        await channel.edit(category=selected_category)
        await channel.send(f"Channel '{channel.name}' moved to category '{selected_category.name}'")


async def find_place(channel):
    """
    Prompts the user to select a region and storage location for a stockpile.

    Args:
    - channel: The Discord channel where the interaction is taking place.

    Returns:
    A tuple containing the selected storage name and region.
    """
    x_side = sides_values.get(channel.guild.id, 'WARDENS')
    r_names = controlled_regions(x_side)
    names1 = r_names[0]
    names2 = r_names[1]
    view = PaginatedButtonsView(names1)
    re_message = await channel.send("Select a region:", view=view)
    await view.wait()

    region = view.selected_item
    region_index = names1.index(region)
    region2 = names2[region_index]
    await re_message.delete()

    if region is None:
        t_msg = await channel.send("No selection made or operation cancelled.")
        asyncio.create_task(delete_after_delay(t_msg, 10))
        return

    s_names = region_storages(region2, x_side)
    view = CustomView(s_names)
    st_message = await channel.send("And to be specific:", view=view)
    await view.wait()

    selected_name = view.selected_item
    await st_message.delete()

    return selected_name, region


async def scheduled_fetch_n_save():
    """
    Periodically fetches data from an API and saves it.
    """
    while True:
        print(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), 'Fetching data from foxhole API')
        await fetch_n_save()
        await asyncio.sleep(3600)


async def scheduled_backup():
    """
    Periodically backs up data to JSON files.
    """
    while True:
        await asyncio.sleep(300)
        await save_backups()


async def save_backups():
    """
    Saves current data structures to JSON files.
    """
    print(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), 'Saving discord data')
    save_to_json(fxpl_values, fxpl_file_name, file_path)
    print('fxpl data saved')
    save_to_json(sides_values, sides_file_name, file_path)
    print('sides data saved')
    save_to_json(channel_expirations, channels_file_name, file_path)
    print('channels data saved')


async def load_backups():
    """
    Loads data structures from JSON files.
    """
    print('Loading from json')
    global fxpl_values, sides_values, channel_expirations
    fxpl_values = load_from_json(fxpl_file_name, file_path)
    if fxpl_values is None:
        fxpl_values = {}
    fxpl_values = {int(k): v for k, v in fxpl_values.items()}
    sides_values = load_from_json(sides_file_name, file_path)
    if sides_values is None:
        sides_values = {}
    sides_values = {int(k): v for k, v in sides_values.items()}
    channel_expirations = load_from_json(channels_file_name, file_path)
    if channel_expirations is None:
        channel_expirations = {}
    channel_expirations = {int(k): {"timestamp": int(v["timestamp"])} for k, v in channel_expirations.items()}


async def re_timer():
    """
    Initiates the channel expiration check task.
    """
    asyncio.create_task(delete_channel_if_expired())


@bot.command()
@commands.has_permissions(administrator=True)
async def betray(ctx):
    """
    Allows an administrator to change the server's side (WARDENS or COLONIALS).

    Args:
    - ctx: The context of the command.
    """
    if ctx.guild is None:
        await ctx.send("This command can only be used in a server.")
        return

    view = CustomView(warden_collies)
    sides_message = await ctx.send("Choose your discord's side:", view=view)
    await view.wait()
    await sides_message.delete()

    selected_side = view.selected_item
    global sides_values
    sides_values[ctx.guild.id] = selected_side
    await ctx.send(f"Value changed to {selected_side}.")


@bot.command()
@commands.has_permissions(administrator=True)
async def fxplc(ctx, nfxpl):
    """
    Allows an administrator to change the fxpl value for the server.

    Args:
    - ctx: The context of the command.
    - nfxpl: The new fxpl value.
    """
    if ctx.guild is None:
        await ctx.send("This command can only be used in a server.")
        return

    if len(nfxpl) < 4:
        await ctx.send("Provide a single argument with at least 4 characters.")
        return

    global fxpl_values
    fxpl_values[ctx.guild.id] = nfxpl
    await ctx.send(f"Value changed to {nfxpl}.")


@bot.command()
async def stockpile(ctx, *args):
    """
    Handles the stockpile command, which can create a stockpile channel with or without an image.

    Args:
    - ctx: The context of the command.
    - *args: Additional arguments provided with the command.
    """
    await ctx.message.delete()

    if ctx.message.attachments:
        image_attachment = ctx.message.attachments[0]
        async with aiohttp.ClientSession() as session:
            async with session.get(image_attachment.url) as resp:
                if resp.status != 200:
                    t_msg = await ctx.send("Failed to download the image.")
                    asyncio.create_task(delete_after_delay(t_msg, 10))
                    return
                data = await resp.read()

        temp_image_path = 'temp_image.png'
        with open(temp_image_path, 'wb') as temp_file:
            temp_file.write(data)

        found_texts, options, contrast_level = extract_text_with_conditions(temp_image_path)
        if len(found_texts) < 2:
            t_msg = await ctx.send("Image processing failed to find enough data.")
            asyncio.create_task(delete_after_delay(t_msg, 10))
            return

        t_name = found_texts[0]
        t_code = found_texts[1]
        t_args = found_texts[2:]

        view = CustomView(yes_or_no)
        yn_message = await ctx.send(f"Would you like to change the stockpile's name? ({t_name}):", view=view)
        await view.wait()
        await yn_message.delete()

        if view.selected_item == 'Yes':
            nn_message = await ctx.send('Please enter the new name for the stockpile:')
            try:
                msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
                t_name = msg.content
                await msg.delete()
                await nn_message.delete()
            except asyncio.TimeoutError:
                await nn_message.delete()
                return

        await create_stockpile_channel(ctx, t_name, t_code, t_args)
    else:
        end_args = combine_and_split(args) if 'combine_and_split' in globals() else args
        if len(end_args) < 2:
            await ctx.send("Provide at least two arguments: name and code. Extra information can be separated by commas.")
            return

        t_name = end_args[0]
        t_code = end_args[1]
        t_args = end_args[2:]

        await create_stockpile_channel(ctx, t_name, t_code, t_args)


@bot.event
async def on_raw_reaction_add(payload):
    """
    Handles raw reaction adds for refreshing stockpile expiration.

    Args:
    - payload: The payload of the reaction add event.
    """
    global channel_expirations
    channel_id = payload.channel_id
    message_id = payload.message_id
    user_id = payload.user_id

    channel = bot.get_channel(channel_id)
    if channel is None:
        channel = await bot.fetch_channel(channel_id)

    if isinstance(channel, discord.TextChannel):
        message = await channel.fetch_message(message_id)
        if message.author.id == bot.user.id and channel_id in channel_expirations:
            new_end_timestamp = time.time() + timedelta(hours=48).total_seconds()
            channel_expirations[channel_id]['timestamp'] = new_end_timestamp
            channel_expirations[channel_id].pop('notified', None)
            channel_expirations[channel_id].pop('final notice', None)
            discord_timestamp = f"<t:{int(new_end_timestamp)}:F>"
            await channel.send(f"The timer has been refreshed. This stockpile now expires on {discord_timestamp}.")


@bot.event
async def on_message(message):
    """
    Processes messages to handle specific commands or interactions.

    Args:
    - message: The message that triggered the event.
    """
    if message.guild is None or message.author == bot.user:
        return

    fxpl = fxpl_values.get(message.guild.id, "fxpl")
    if message.channel.name.startswith(fxpl) and len(message.attachments) > 0:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                await message.delete()
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status != 200:
                            return
                        data = await resp.read()

                temp_image_path = 'temp_image.png'
                with open(temp_image_path, 'wb') as temp_file:
                    temp_file.write(data)

                found_texts, options, contrast_level = extract_text_with_conditions(temp_image_path)
                if len(found_texts) < 2:
                    return

                t_name = found_texts[0]
                t_code = found_texts[1]
                t_args = found_texts[2:]

                await create_stockpile_channel(message.channel, t_name, t_code, t_args)

    await bot.process_commands(message)


@bot.event
async def on_ready():
    """
    Executes actions when the bot is ready.
    """
    print(f'Logged in as {bot.user.name}')
    await load_backups()
    await asyncio.sleep(5)
    await re_timer()
    asyncio.create_task(scheduled_backup())
    await scheduled_fetch_n_save()



# Replace 'DISCORD_SECRET_KEY' with your actual bot key
bot.run('DISCORD_SECRET_KEY')