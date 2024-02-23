##                                                           ##
##           wokring version with buttons revision           ##
## combined effort of Atroci and Mugna for the common Warden ##
##             ---------------------------------             ##
##                                                           ##

import discord
from discord.ext import commands
from discord.ui import Button, View
import aiohttp
import asyncio
from datetime import timedelta
import time
from cbut import CustomView, CustomButton
from sman import combine_and_split
from imger import extract_text_with_conditions

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.message_content = True

yes_or_no = ['Yes','No']  # Yes or no list for a yes or no question button
fxpl = 'fxpl'

bot = commands.Bot(command_prefix='!', intents=intents)

fxpl_values = {}

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

async def delete_after_delay(msg, delay):
    await asyncio.sleep(delay)
    await msg.delete()

async def create_stockpile_channel(ctx, t_name, t_code, t_args):
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

    asyncio.create_task(delete_channel_if_expired(channel.id))

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

                    view = CustomView(yes_or_no)
                    yn_message = await message.channel.send(f"Would you like to add information? (i.e. location, usage...).", view=view)
                    await view.wait()
                    await yn_message.delete()

                    if view.selected_item == 'Yes':
                        def check(m):
                            # Ensure the message is from the same user and channel
                            return m.author == message.author and m.channel == message.channel

                        ei_message = await message.channel.send('Can do. What do you want to add?:')

                        try:
                            # Wait for a response from the user
                            msg = await bot.wait_for('message', check=check, timeout=120.0)  # 120 seconds timeout
                            t_args.insert(0, msg.content)  # This adds msg.content at the first position of the list t_args
                            await msg.delete()
                            await ei_message.delete()
                            t_msg = await message.channel.send('Got it buddy.')
                            asyncio.create_task(delete_after_delay(t_msg, 10))
                        except asyncio.TimeoutError:
                            await ei_message.delete()
                            t_msg = await message.channel.send('Sorry, you had 2 minutes to make your point. I will just continue.')  # Corrected ctx.send to message.channel.send
                            asyncio.create_task(delete_after_delay(t_msg, 10))
                            print('User took too much time to add information (120 seconds)')

                    if view.selected_item == 'No':
                        print('User did not add information')

                t_m_channel = message.channel
                if t_m_channel.guild is None:
                    t_msg = await t_m_channel.send("This command can only be used in a server.")
                    asyncio.create_task(delete_after_delay(t_msg, 10))
                    return

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

                    asyncio.create_task(delete_channel_if_expired(channel.id))
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

                asyncio.create_task(delete_channel_if_expired(channel.id))

    # Important: This line is required to allow other on_message commands to run.
    await bot.process_commands(message)

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
bot.run('YOUR_BOT_TOKEN')
