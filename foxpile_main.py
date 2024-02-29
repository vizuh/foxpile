##                                                           ##
##           wokring version with buttons revision           ##
## combined effort of Atroci and Mugna for the common Warden ##
##             includes bot token so keep secret             ##
##            This is a working version 27/02/2024           ##
##                   --- New Features: ---                   ##
##                  database for stockpiles                  ##
##                   --- Need To Add: ---                    ##
##                  features for facilities                  ##


import discord
from discord.ext import commands
from discord.ui import Button, View
import aiohttp
import asyncio
import datetime
from datetime import timedelta
import time
import os
from dotenv import load_dotenv
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

warden_collies = ['WARDENS' , 'COLONIALS']
yes_or_no = ['Yes','No']  # Yes or no list for a yes or no question button
fxpl = 'fxpl'

bot = commands.Bot(command_prefix='!', intents=intents)


load_dotenv()
file_path = os.getenv('FILE_PATH')


fxpl_values = {}
fxpl_file_name = 'fxpl.json'

sides_values = {}
sides_file_name = 'sides.json'

channel_expirations = {}
channels_file_name = 'channels.json'



class RefreshButton(View):
    """ This is only here because i yet to integrate another module for sharing better. """
    """ Will be moved to ui_elements.py later on in the future. This is only for now """
    """ This might replace the on_reaction event if it will work after bot restarts """
    def __init__(self, channel_id):
        super().__init__()
        self.channel_id = channel_id
        self.timeout = None

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.green, custom_id="refresh_button")
    async def refresh_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        print(f'Clicked on {self.channel_id}')
        channel_id = self.channel_id
        await button.response.edit_message(content=f'Refreshing',view=None)
        channel = bot.get_channel(channel_id)
        new_end_timestamp = time.time() + timedelta(hours=48).total_seconds()
        channel_expirations[channel_id]['timestamp'] = new_end_timestamp
        channel_expirations[channel_id].pop('notified', None)
        channel_expirations[channel_id].pop('final_notice', None)
        discord_timestamp = f"<t:{int(new_end_timestamp)}:F>"
        await channel.send(content=f'Channel has been refreshed. Stockpile will expire on {discord_timestamp}',view=self)



async def delete_channel_if_expired():
    """Deletes the channel if the current time is past the end_timestamp and sends a notification 12 hours before."""
    global channel_expirations
    while True:
        print(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), 'Running expirations.')
        for channel_id in list(channel_expirations.keys()):  # Use list() to avoid runtime error for changing dict size
            print(f'iterating for {channel_id}')
            end_timestamp = channel_expirations[channel_id]['timestamp']
            time_left = end_timestamp - time.time()

            if time_left <= 0:
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.delete(reason="Time expired for this channel.")
                del channel_expirations[channel_id]  # Remove the channel from tracking
                break  # Assuming this is part of a loop that you want to exit
            else:
                try:
                    if time_left <= 18460 and not channel_expirations[channel_id]['final notice'] == 'True':
                        channel = bot.get_channel(channel_id)
                        if channel:
                            await channel.send("@everyone, this channel will expire in about 5 hours!")
                            channel_expirations[channel_id]['final notice'] = 'True'
                    elif time_left <= 43460 and not channel_expirations[channel_id]['notified'] == 'True':
                        channel = bot.get_channel(channel_id)
                        if channel:
                            await channel.send("@here, this channel will expire in about 12 hours!")
                            channel_expirations[channel_id]['notified'] = 'True'
                except KeyError:
                    continue
        await asyncio.sleep(300)  # Wait for 5 minutes before checking again


async def delete_after_delay(msg, delay):
    await asyncio.sleep(delay)
    await msg.delete()


async def create_stockpile_channel(ctx, t_name, t_code, t_args):
    global channel_expirations
    if ctx.guild is None:
        t_msg = await ctx.send("This command can only be used in a server.")
        asyncio.create_task(delete_after_delay(t_msg, 10))
        return

    items = ctx.author.roles  # Or any list of items you want to use for selection
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

    asyncio.create_task(allow_refresh(channel.id))


async def allow_refresh(channel_id):
    global channel_expirations
    while True:
        channel = bot.get_channel(channel_id)
        try:
            async for message in channel.history(limit=1000):
                if message.author.bot:
                    # Found the last bot message.
                    # Now adding a button to refresh the timer.
                    view = RefreshButton(channel_id)
                    await message.edit(content=message.content, view=view)
                    break

            print(f"Channel:{channel_id} can be refreshed.")
        except AttributeError:
            del channel_expirations[channel_id]
            print(f"Channel:{channel_id} was not found and therefore deleted.")
        await asyncio.sleep(860) # sleep for a bit less than 15 minutes


async def find_place(channel):
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

    s_names = region_storages(region2,x_side)
    view = CustomView(s_names)
    st_message = await channel.send("And to be specific:", view=view)
    await view.wait()

    selected_name = view.selected_item
    await st_message.delete()

    return selected_name , region


async def scheduled_fetch_n_save():
    while True:
        print(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),'Fetching data from foxhole API')
        await fetch_n_save()
        await asyncio.sleep(3600)  # Sleep for 1 hour


async def scheduled_backup():
    while True:
        await asyncio.sleep(300)  # Sleep for 5 minutes
        await save_backups()


async def save_backups():
    print(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),'Saving discord data')
    save_to_json(fxpl_values,fxpl_file_name,file_path)
    print('fxpl data saved')
    save_to_json(sides_values,sides_file_name,file_path)
    print('sides data saved')
    save_to_json(channel_expirations, channels_file_name,file_path)
    print('channels data saved')


async def load_backups():
    print('Loading from json')
    global fxpl_values
    global sides_values
    global channel_expirations
    fxpl_values = load_from_json(fxpl_file_name,file_path)
    if fxpl_values is None:
        fxpl_values = {}
    fxpl_values = {int(k): v for k, v in fxpl_values.items()} ## convert the keys in the dictionary to integers
    sides_values = load_from_json(sides_file_name,file_path)
    if sides_values is None:
        sides_values = {}
    sides_values = {int(k): v for k, v in sides_values.items()}  ## convert the keys in the dictionary to integers
    channel_expirations = load_from_json(channels_file_name,file_path)
    if channel_expirations is None:
        channel_expirations = {}
    channel_expirations = {int(k): {"timestamp": int(v["timestamp"])} for k, v in channel_expirations.items()} ## convert the keys in the dictionary to integers


async def re_timer():
    asyncio.create_task(delete_channel_if_expired())
    for channel_id in channel_expirations.keys():

        print(f"Channel: {channel_id} is on the timer again")
        asyncio.create_task(allow_refresh(channel_id))



@bot.command()
@commands.has_permissions(administrator=True)
async def betray(ctx):
    # Ensure we're in a server context
    if ctx.guild is None:
        await ctx.send("This command can only be used in a server.")
        return

    view = CustomView(warden_collies)
    sides_message = await ctx.send(f"Choose your discord's side:", view=view)
    await view.wait()
    await sides_message.delete()

    if view.selected_item == 'WARDENS':
        n_side = 'WARDENS'
    if view.selected_item == 'COLONIALS':
        n_side = 'COLONIALS'

    # Update the sides value for the server
    global sides_values
    sides_values[ctx.guild.id] = n_side
    await ctx.send(f"Value changed to {n_side} .")


@bot.command()
@commands.has_permissions(administrator=True)
async def fxplc(ctx, nfxpl):
    # Ensure we're in a server context
    if ctx.guild is None:
        await ctx.send("This command can only be used in a server.")
        return

    # Check if the new fxpl value is valid
    if len(nfxpl) < 4:
        await ctx.send("Provide a single argument with at least 4 characters.")
        return

    # Update the fxpl value for the server
    global fxpl_values
    fxpl_values[ctx.guild.id] = nfxpl
    await ctx.send(f"Value changed to {nfxpl} .")


@bot.command()
async def stockpile(ctx, *args):
    await ctx.message.delete()

    if ctx.message.attachments:
        # If there's an attachment, process as !stockimg logic
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

        # Assuming 'extract_text_with_conditions' is defined and works as described
        found_texts, options, contrast_level = extract_text_with_conditions(temp_image_path)
        response_message = f"Found texts: {found_texts}\nApplied Filter: {options['filter_type']}, Gamma: {options['gamma']}, Contrast: {contrast_level}"
        print (response_message)



        if len(found_texts) < 2:
            t_msg = await ctx.send("Image processing failed to find enough data.")
            asyncio.create_task(delete_after_delay(t_msg, 10))
            return

        t_name = found_texts[0]
        t_code = found_texts[1]
        t_args = found_texts[2:]

        view = CustomView(yes_or_no)
        yn_message = await ctx.send(f"Would you like to change the stockpile's name?({t_name}):", view=view)
        await view.wait()
        await yn_message.delete()


        if view.selected_item == 'Yes':
            def check(m):
                # Ensure the message is from the same user and channel
                return m.author == ctx.author and m.channel == ctx.channel

            t_args.insert(0, t_name) # Adding the name recorded to the extra info

            nn_message = await ctx.send('Please enter the new name for the stockpile:')

            try:
                # Wait for a response from the user
                msg = await bot.wait_for('message', check=check, timeout=60.0)  # 60 seconds timeout
                t_name = msg.content  # Update t_name with the user's response
                await msg.delete()
                await nn_message.delete()
                t_msg = await ctx.send(f'Stockpile name changed to: {t_name}')
                asyncio.create_task(delete_after_delay(t_msg, 10))
            except asyncio.TimeoutError:
                await nn_message.delete()
                t_msg = await ctx.send('Sorry, you took too long to respond.')
                asyncio.create_task(delete_after_delay(t_msg, 10))
                print ('User took too much time to change name')
                return

        if view.selected_item == 'No':
            print ('User did not change stockpile name')

        view = CustomView(yes_or_no)
        yn_message = await ctx.send(f"Would you like to add information? (i.e. location, usage...).", view=view)
        await view.wait()
        await yn_message.delete()


        if view.selected_item == 'Yes':
            def check(m):
                # Ensure the message is from the same user and channel
                return m.author == ctx.author and m.channel == ctx.channel

            ei_message = await ctx.send('Can do. What do you want to add?:')

            try:
                # Wait for a response from the user
                msg = await bot.wait_for('message', check=check, timeout=120.0)  # 60 seconds timeout
                t_args.insert(0, msg.content)  # This adds msg.content at the first position of the list t_args
                await msg.delete()
                await ei_message.delete()
                t_msg = await ctx.send(f'Got it buddy.')
                asyncio.create_task(delete_after_delay(t_msg, 10))
            except asyncio.TimeoutError:
                await ei_message.delete()
                t_msg = await ctx.send('Sorry, you had 2 minutes to make your point. I will just continue.')
                asyncio.create_task(delete_after_delay(t_msg, 10))
                print ('User took too much time to add information (120 seconds)')


        if view.selected_item == 'No':
            print ('User did not add information')

    else:
        # Continue with normal !stockpile logic if no image
        print(args)
        end_args = combine_and_split(
            args) if 'combine_and_split' in globals() else args  # Assumes combine_and_split is defined
        if len(end_args) < 2:
            await ctx.send(
                "For using me with text you will need to provide at least two arguments: (name,code). Extra information can be provided if separated via commas. Example '!stockpile [NSR]Logi,123456,Callum Cape's Seaport,Stored 1k rmats for a trade with FMAT")
            return

        t_name = end_args[0]
        t_code = end_args[1]
        t_args = end_args[2:]

    await create_stockpile_channel(ctx, t_name, t_code, t_args)



@bot.event
async def on_message(message):
    global channel_expirations
    # Skip if message is not from a guild or if it's from the bot itself
    if message.guild is None or message.author == bot.user:
        return
    # Check if the message is sent in a channel whose name starts with "fxpl" or defined prefix
    fxpl = fxpl_values.get(message.guild.id, "fxpl")
    if message.channel.name.startswith(fxpl):
        # Check if there are any attachments in the message
        if len(message.attachments) > 0:
            for attachment in message.attachments:
                # Assuming you're looking for image files
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                    image_attachment = message.attachments[0]
                    await message.delete()
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_attachment.url) as resp:
                            if resp.status != 200:
                                t_msg = await message.channel.send("Failed to download the image.")
                                asyncio.create_task(delete_after_delay(t_msg, 10))
                                return
                            data = await resp.read()

                    temp_image_path = 'temp_image.png'
                    with open(temp_image_path, 'wb') as temp_file:
                        temp_file.write(data)


                    found_texts, options, contrast_level = extract_text_with_conditions(temp_image_path)
                    response_message = f"Found texts: {found_texts}\nApplied Filter: {options['filter_type']}, Gamma: {options['gamma']}, Contrast: {contrast_level}"
                    print(response_message)

                    if len(found_texts) < 2:
                        t_msg = await message.channel.send("Image processing failed to find enough data.")
                        asyncio.create_task(delete_after_delay(t_msg, 10))
                        return

                    t_name = found_texts[0]
                    t_code = found_texts[1]
                    t_args = found_texts[2:]

                    view = CustomView(yes_or_no)
                    yn_message = await message.channel.send(f"Would you like to change the stockpile's name?({t_name}):", view=view)
                    await view.wait()
                    await yn_message.delete()

                    if view.selected_item == 'Yes':
                        def check(m):
                            # Ensure the message is from the same user and channel
                            return m.author == message.author and m.channel == message.channel

                        t_args.insert(0, t_name)  # Adding the name recorded to the extra info

                        nn_message = await message.channel.send('Please enter the new name for the stockpile:')

                        try:
                            # Wait for a response from the user
                            msg = await bot.wait_for('message', check=check, timeout=60.0)  # 60 seconds timeout
                            t_name = msg.content  # Update t_name with the user's response
                            await msg.delete()
                            await nn_message.delete()
                            t_msg = await message.channel.send(f'Stockpile name changed to: {t_name}')
                            asyncio.create_task(delete_after_delay(t_msg, 10))
                        except asyncio.TimeoutError:
                            await nn_message.delete()
                            t_msg = await message.channel.send('Sorry, you took too long to respond.')
                            asyncio.create_task(delete_after_delay(t_msg, 10))
                            print('User took too much time to change name')
                            return

                    if view.selected_item == 'No':
                        print('User did not change stockpile name')



                t_m_channel = message.channel
                if t_m_channel.guild is None:
                    t_msg = await t_m_channel.send("This command can only be used in a server.")
                    asyncio.create_task(delete_after_delay(t_msg, 10))
                    return

                s_locations = await find_place(t_m_channel)
                t_args.insert(0, s_locations)

                items = message.author.roles
                items.insert(0, "None")
                view = CustomView(items)
                r_message = await t_m_channel.send("Select the role that will see this stockpile(or None):", view=view)
                await view.wait()

                selected_role = view.selected_item
                await r_message.delete()

                if selected_role is None:
                    t_msg = await t_m_channel.send("No selection made or operation cancelled.")
                    asyncio.create_task(delete_after_delay(t_msg, 10))
                    return

                if selected_role == "None":
                    print('User selected None for roles')
                    overwrites = {
                        message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        message.author: discord.PermissionOverwrite(read_messages=True)
                    }

                    channel = await message.guild.create_text_channel(t_name, category=message.channel.category,
                                                                      overwrites=overwrites)
                    end_timestamp = time.time() + timedelta(hours=48).total_seconds()
                    channel_expirations[channel.id] = {'timestamp': end_timestamp}

                    discord_timestamp = f"<t:{int(end_timestamp)}:F>"
                    await channel.send(f"Stockpile Code: {t_code}. This stockpile expires on {discord_timestamp}.")

                    for index, arg in enumerate(t_args, start=1):
                        await channel.send(f'Extra info {index}: {arg}')

                    asyncio.create_task(allow_refresh(channel.id))
                    return

                #If an actual role was chosen
                overwrites = {
                    message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    selected_role: discord.PermissionOverwrite(read_messages=True)
                }

                channel = await message.guild.create_text_channel(t_name, category=message.channel.category, overwrites=overwrites)
                end_timestamp = time.time() + timedelta(hours=48).total_seconds()
                channel_expirations[channel.id] = {'timestamp': end_timestamp}

                discord_timestamp = f"<t:{int(end_timestamp)}:F>"
                await channel.send(f"Stockpile Code: {t_code}. This stockpile expires on {discord_timestamp}.")

                for index, arg in enumerate(t_args, start=1):
                    await channel.send(f'Extra info {index}: {arg}')

                asyncio.create_task(allow_refresh(channel.id))

    # Important: This line is required to allow other on_message commands to run.
    await bot.process_commands(message)


@bot.event
async def on_reaction_add(reaction, user):
    if user != bot.user and reaction.message.channel.id in channel_expirations:
        print(f'reaction captured in channel {reaction.message.channel.id}')
        new_end_timestamp = time.time() + timedelta(hours=48).total_seconds()
        channel_expirations[reaction.message.channel.id]['timestamp'] = new_end_timestamp
        channel_expirations[reaction.message.channel.id].pop('notified', None)
        channel_expirations[channel_id].pop('final_notice', None)
        discord_timestamp = f"<t:{int(new_end_timestamp)}:F>"
        await reaction.message.channel.send(
            f"The timer has been refreshed. This stockpile now expires on {discord_timestamp}.")


@bot.event
async def on_ready():
    await bot.load_extension("foxility_cog")
    print(f'Logged in as {bot.user.name}')
    await load_backups()
    print('Step-1. Backups loaded...')
    await re_timer()
    print('Step-2. Timers and Refreshers loaded...')
    asyncio.create_task(scheduled_backup())
    print('Ready AF')
    await scheduled_fetch_n_save()
    print('stEp tHrEe cOmPlEtE')



# Replace 'YOUR_BOT_TOKEN' with your actual bot token
#bot.run(bot_token)
bot.run(os.getenv('DISCORD_SECRET_KEY'))
