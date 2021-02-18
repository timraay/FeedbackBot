import discord
from discord.ext import commands
import asyncio
import re
import json

from feedback import models
from utils import add_empty_fields, int_to_emoji, ask_reaction, ask_message
from cogs._events import CustomException

async def show_feeds(ctx):
    embed = discord.Embed()
    feeds = models.Guild(ctx.guild.id).feeds
    if feeds:
        embed.title = f"This guild has {str(len(feeds))} feeds."
        embed.description = ""
        for i, feed in enumerate(feeds):
            channel = ctx.guild.get_channel(feed.feed_channel_id)
            if channel: channel = channel.mention
            else: channel = "No channel ⚠️"
            embed.description += f'**#{str(i+1)}** | {feed.feed_name} (`{feed.feed_shortname}`) - {channel}\n'
    else:
        embed.title = "This guild doesn't have any feeds yet!"
        embed.description = f"You can create one by typing `{ctx.prefix}feeds create`."
        embed.add_field(name="What is a feed?", value="A feed is a text channel where guild members can submit feedback to.")

    await ctx.send(embed=embed)
async def show_labels(ctx, feed):
    labels = feed.labels
    embed = discord.Embed(color=discord.Color(int(feed.feed_color, 16)))
    embed.set_footer(text=f"Feed: {feed.feed_name} - ID: {feed.feed_shortname}")
    if labels:
        embed.title = f"This feed has {str(len(labels))} labels."
        embed.description = ""
        for i, label in enumerate(labels):
            embed.description += f'**#{str(i+1)}** | {label.label_emoji} {label.label_name} (`{label.label_shortname}`)\n'
    else:
        embed.title = "This feed doesn't have any labels yet!"
        embed.description = f"You can create one by typing `{ctx.prefix}feed {feed.feed_shortname} labels create`."
        embed.add_field(name="What is a label?", value="A label is a tag users can attach to their feedback to further categorize it. It may also show extra information to the user while they are creating the feedback.")

    await ctx.send(embed=embed)
async def show_triggers(ctx):
    guild = models.Guild(ctx.guild.id)
    triggers = guild.triggers

    embed = discord.Embed()
    if triggers:
        embed.title = f"This guild has {str(len(triggers))} triggers."
        embed.description = ""
        for i, trigger in enumerate(triggers):
            try: message = await commands.MessageConverter().convert(ctx, f'{trigger.trigger_channel_id}-{trigger.trigger_message_id}')
            except commands.BadArgument: message = None
            if message: jump = f"[Jump to message]({message.jump_url})"
            else: jump = "No message ⚠️"
            embed.description += f'**#{str(i+1)}** | {trigger.trigger_emoji} {trigger.feed.feed_name} - {jump}\n'
    else:
        embed.title = "This guild doesn't have any triggers yet!"
        embed.description = f"You can create one by typing `{ctx.prefix}trigger create`."
        embed.add_field(name="What is a trigger?", value="A trigger is a reaction under a message users can click to start creating their feedback, instead of having to run a command.")

    await ctx.send(embed=embed)

async def show_feed(ctx, feed):
    color = discord.Color(int(feed.feed_color, 16)) if feed.feed_color else discord.Embed.Empty
    channel = ctx.guild.get_channel(feed.feed_channel_id)
    channel = channel.mention if channel else "No channel ⚠️"
    embed = discord.Embed(color=color, title=f"#{str(feed.index+1)} | {feed.feed_name} (`{feed.feed_shortname}`)", description=f'''\nColor: **#{feed.feed_color}**\nChannel: **{channel}**\nAnonymous: **{"Yes" if feed.anonymous else "No"}**\nReactions: **{feed.reactions if feed.reactions else "None"}**\n\nDescription:\n{feed.feed_desc if feed.feed_desc else "No description."}''')
    if feed.feed_desc_url: embed.set_image(url=feed.feed_desc_url)
    await ctx.send(embed=embed)
async def show_label(ctx, feed, label):
    color = discord.Color(int(label.label_color, 16)) if label.label_color else discord.Embed.Empty
    embed = discord.Embed(color=color, title=f"#{str(feed.index+1)} | {label.label_name} (`{label.label_shortname}`)", description=f'''\nColor: **#{label.label_color}**\nEmoji: {label.label_emoji}\n\nDescription:\n{label.label_desc if label.label_desc else "No description."}''')
    embed.set_footer(text=f"Feed: {feed.feed_name} - ID: {feed.feed_shortname}")
    if label.label_desc_url: embed.set_image(url=label.label_desc_url)
    await ctx.send(embed=embed)
async def show_trigger(ctx, trigger):
    feed = trigger.feed
    try: message = await commands.MessageConverter().convert(ctx, f'{trigger.trigger_channel_id}-{trigger.trigger_message_id}')
    except commands.BadArgument: message = None
    if message: jump = f"[Jump to message]({message.jump_url})"
    else: jump = "No message ⚠️"
    embed = discord.Embed(title=f"#{str(trigger.index+1)} | {trigger.trigger_emoji} {feed.feed_name}", description=f'''\n{jump}''')
    embed.set_footer(text=f"Feed: {feed.feed_name} - ID: {feed.feed_shortname}")
    await ctx.send(embed=embed)

async def create_feed(ctx):
    # feed_name
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new feed... (1/7)")
    embed.add_field(name="What should the feed's name be?", value="Keep it short. 20 characters max.")
    feed_name = await ask_message(ctx, embed=embed)
    if feed_name == None: return
    def validate_name():
        if len(feed_name) < 1 or len(feed_name) > 20: return f"Invalid length! 20 characters max, you have {len(feed_name)}."
        else: return None
    error = validate_name()
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        feed_name = await ask_message(ctx, embed)
        if feed_name == None: return
        error = validate_name()
    
    # feed_shortname
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new feed... (2/7)")
    embed.add_field(name="What should the feed's short name be?", value="This will be used to reference to it using commands. You may only use lowercase characters, digits, underscores and dashes. No spaces.")
    feed_shortname = await ask_message(ctx, embed=embed)
    if feed_shortname == None: return
    def validate_shortname():
        if len(feed_shortname) < 1 or len(feed_shortname) > 20: return f"Invalid length! 20 characters max, you have {len(feed_shortname)}."
        if not re.match(r"[a-z0-9_-]+$", feed_shortname): return "Invalid character(s)! You can only use [a-z0-9_-]."
        try: int(feed_shortname)
        except ValueError: pass
        else: return "Your name can't fully consist of numbers!"
        try: models.Feed.find(ctx.guild.id, feed_shortname)
        except models.NotFound: pass
        else: return "A feed with this short name already exists!"
        return None
    error = validate_shortname()
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        feed_shortname = await ask_message(ctx, embed)
        if feed_shortname == None: return
        error = validate_shortname()

    # feed_desc
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new feed... (3/7)")
    embed.add_field(name="What description should the feed have?", value="This will be shown to anyone trying to create feedback for this feed.")
    feed_desc, feed_desc_url = await ask_message(ctx, embed=embed, allow_image=True)
    if feed_desc == None: return
    def validate_desc():
        if len(feed_desc) > 1500: return f"Invalid length! 1500 characters max, you have {len(feed_desc)}."
        return None
    error = validate_desc()
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        feed_desc, feed_desc_url = await ask_message(ctx, embed, allow_image=True)
        if feed_desc == None: return
        error = validate_desc()
    if not feed_desc_url: feed_desc_url = ""

    # feed_channel_id
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new feed... (4/7)")
    embed.add_field(name="What channel should the feed be linked to?", value="Here any new feedback will be sent.")
    feed_channel_id = await ask_message(ctx, embed=embed)
    if feed_channel_id == None: return
    try: feed_channel_id = (await commands.TextChannelConverter().convert(ctx, feed_channel_id)).id
    except commands.BadArgument as e: error = str(e)
    else: error = None
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        feed_channel_id = await ask_message(ctx, embed)
        if feed_channel_id == None: return
        try: feed_channel_id = (await commands.TextChannelConverter().convert(ctx, feed_channel_id)).id
        except commands.BadArgument as e: error = str(e)
        else: error = None

    # feed_color
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new feed... (5/7)")
    embed.add_field(name="What should the feed's color be?", value="This will be the default color any feedback on this feed will have. You need to pick one of the presets, type [a color hex code](https://htmlcolorcodes.com/color-picker/) (eg. #71e30a), or type \"default\" for no color.\n\nAvailable presets:\nteal, dark_teal, green, dark_green, blue, dark_blue, purple, dark_purple, magenta, dark_magenta, yellow, dark_yellow, gold, dark_gold, orange, dark_orange, red, dark_red, lighter_gray, light_gray, dark_gray, darker_gray, blurple, grayple, white, black")
    feed_color = await ask_message(ctx, embed=embed)
    if feed_color == None: return
    def validate_color(feed_color):
        feed_color = feed_color.lower()
        if feed_color == "teal": feed_color = "#1abc9c"
        elif feed_color == "dark_teal": feed_color = "#11806a"
        elif feed_color == "green": feed_color = "#2ecc71"
        elif feed_color == "dark_green": feed_color = "#1f8b4c"
        elif feed_color == "blue": feed_color = "#3498db"
        elif feed_color == "dark_blue": feed_color = "#206694"
        elif feed_color == "purple": feed_color = "#9b59b6"
        elif feed_color == "dark_purple": feed_color = "#71368a"
        elif feed_color == "magenta": feed_color = "#e91e63"
        elif feed_color == "dark_magenta": feed_color = "#ad1457"
        elif feed_color == "yellow": feed_color = "#f5ef42"
        elif feed_color == "dark_yellow": feed_color = "#a6a126"
        elif feed_color == "gold": feed_color = "#f1c40f"
        elif feed_color == "dark_gold": feed_color = "#c27c0e"
        elif feed_color == "orange": feed_color = "#e67e22"
        elif feed_color == "dark_orange": feed_color = "#a84300"
        elif feed_color == "red": feed_color = "#e74c3c"
        elif feed_color == "dark_red": feed_color = "#992d22"
        elif feed_color in ["lighter_gray", "lighter_grey"]: feed_color = "#95a5a6"
        elif feed_color in ["light_gray", "light_grey"]: feed_color = "#979c9f"
        elif feed_color in ["dark_gray", "dark_grey"]: feed_color = "#607d8b"
        elif feed_color in ["darker_gray", "darker_grey"]: feed_color = "#546e7a"
        elif feed_color == "blurple": feed_color = "#7289da"
        elif feed_color in ["grayple", "greyple"]: feed_color = "#99aab5"
        elif feed_color == "white": feed_color = "#fffffe"
        elif feed_color == "black": feed_color = "#000000"
        elif feed_color in ["default", "none"]: feed_color = "#ffffff"
        if feed_color.startswith("0x"): feed_color = feed_color.replace("0x", "#", 1)

        if not feed_color.startswith("#"): return "Invalid preset! Make sure it's in the above list or check your spelling.", feed_color.replace("#", "", 1)
        feed_color = feed_color.replace("#", "", 1)
        if not re.match(r"[0-9a-f]{6}$", feed_color): return "Invalid hex code!", feed_color
        return None, feed_color

    error, feed_color = validate_color(feed_color)
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        feed_color = await ask_message(ctx, embed)
        if feed_color == None: return
        error, feed_color = validate_color(feed_color)
    
    # anonymous
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new feed... (6/7)")
    embed.add_field(name="Should feedback sent to the feed be anonymous?", value="Otherwise it will show the user's name and profile picture.")
    options = {
        "<:yes:809149148356018256>": "Yes, make feedback anonymous",
        "<:no:808045512393621585>": "No, make the user visible"
    }
    feed_anonymous = await ask_reaction(ctx, embed=embed, options=options)
    if feed_anonymous == None: return
    elif feed_anonymous == "<:yes:809149148356018256>": feed_anonymous = 1
    elif feed_anonymous == "<:no:808045512393621585>": feed_anonymous = 0
    else:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name="Didn't recognize response. Please try again.")
        feed_anonymous = await ask_message(ctx, embed)
        if feed_anonymous == None: return
        elif feed_anonymous == "<:yes:809149148356018256>": feed_anonymous == 1
        elif feed_anonymous == "<:no:808045512393621585>": feed_anonymous = 0
        else: raise CustomException("An unexpected error occured!", f"Emoji \"{feed_anonymous}\" was not recognized twice.")
    
    # feed_reactions
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new feed... (7/7)")
    embed.add_field(name="Should feedback sent to the feed have reactions?", value="Type a list of emojis separated by a comma. When using custom emojis the bot must be in the server it is from. For no reactions type \"none\".")
    feed_reactions = await ask_message(ctx, embed=embed)
    if feed_reactions == None: return
    async def validate_reactions(feed_reactions):
        if feed_reactions.lower() == "none":
            return None, ""
        else:
            emojis = [emoji.strip() for emoji in feed_reactions.split(',')]
            converter = commands.EmojiConverter()
            with open('emoji_map.json', 'r') as f:
                emoji_map = json.load(f)
            for emoji in emojis:
                if emoji not in emoji_map.values():
                    try: await converter.convert(ctx, emoji)
                    except commands.BadArgument: return f'Invalid emoji! Can\'t recognize "{emoji}" as an emoji.', None
            return None, ",".join(emojis)
    error, feed_reactions = await validate_reactions(feed_reactions)
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        feed_reactions = await ask_message(ctx, embed)
        if feed_reactions == None: return
        error, feed_reactions = await validate_reactions(feed_reactions)
    


    if validate_shortname():
        raise CustomException("Couldn't create feed!", validate_shortname())

    feed = models.Feed.create(ctx.guild.id, feed_name=feed_name, feed_shortname=feed_shortname, feed_color=feed_color, feed_desc=feed_desc, feed_desc_url=feed_desc_url, feed_channel_id=feed_channel_id, anonymous=feed_anonymous, reactions=feed_reactions)
    embed = discord.Embed(
        color=discord.Color(7844437),
        description=f"You can change the configuration at any time, using the below command:```{ctx.prefix}feed {feed.feed_shortname} <option> <new value>```\nAvailable options: name, shortname, description, channel, color, anonymous, reactions"
    )
    embed.set_author(name=f"Feed \"{feed_name}\" created", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    await ctx.send(embed=embed)
    await show_feed(ctx, feed)
async def create_label(ctx, feed):
    # label_name
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new label... (1/5)")
    embed.add_field(name="What should the label's name be?", value="Keep it short. 20 characters max.")
    label_name = await ask_message(ctx, embed=embed)
    if label_name == None: return
    def validate_name():
        if len(label_name) < 1 or len(label_name) > 20: return f"Invalid length! 20 characters max, you have {len(label_name)}."
        else: return None
    error = validate_name()
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        label_name = await ask_message(ctx, embed)
        if label_name == None: return
        error = validate_name()
    
    # label_shortname
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new label... (2/5)")
    embed.add_field(name="What should the label's short name be?", value="This will be used to reference to it using commands. You may only use lowercase characters, digits, underscores and dashes. No spaces.")
    label_shortname = await ask_message(ctx, embed=embed)
    if label_shortname == None: return
    def validate_shortname():
        if len(label_shortname) < 1 or len(label_shortname) > 20: return f"Invalid length! 20 characters max, you have {len(label_shortname)}."
        if not re.match(r"[a-z0-9_-]+$", label_shortname): return "Invalid character(s)! You can only use [a-z0-9_-]."
        try: int(label_shortname)
        except ValueError: pass
        else: return "Your name can't fully consist of numbers!"
        try: models.Label.find(feed, label_shortname)
        except models.NotFound: pass
        else: return "A label with this short name already exists!"
        return None
    error = validate_shortname()
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        label_shortname = await ask_message(ctx, embed)
        if label_shortname == None: return
        error = validate_shortname()

    # label_desc
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new label... (3/5)")
    embed.add_field(name="What description should the label have?", value="This will be shown in addition to the feed's label once this label is selected. This will replace the feed's image, if any.")
    label_desc, label_desc_url = await ask_message(ctx, embed=embed, allow_image=True)
    if label_desc == None: return
    def validate_desc():
        if len(label_desc) > 1500: return f"Invalid length! 1500 characters max, you have {len(label_desc)}."
        return None
    error = validate_desc()
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        label_desc, label_desc_url = await ask_message(ctx, embed, allow_image=True)
        if label_desc == None: return
        error = validate_desc()
    if not label_desc_url: label_desc_url = ""
    
    # label_color
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new label... (4/5)")
    embed.add_field(name="What should the label's color be?", value="This will be the color any feedback with this label will have. This will overwrite the feed's color, if any. You need to pick one of the presets, type [a color hex code](https://htmlcolorcodes.com/color-picker/) (eg. #71e30a), or type \"default\" for no color.\n\nAvailable presets:\nteal, dark_teal, green, dark_green, blue, dark_blue, purple, dark_purple, magenta, dark_magenta, yellow, dark_yellow, gold, dark_gold, orange, dark_orange, red, dark_red, lighter_gray, light_gray, dark_gray, darker_gray, blurple, grayple, white, black")
    label_color = await ask_message(ctx, embed=embed)
    if label_color == None: return
    def validate_color(label_color):
        label_color = label_color.lower()
        if label_color == "teal": label_color = "#1abc9c"
        elif label_color == "dark_teal": label_color = "#11806a"
        elif label_color == "green": label_color = "#2ecc71"
        elif label_color == "dark_green": label_color = "#1f8b4c"
        elif label_color == "blue": label_color = "#3498db"
        elif label_color == "dark_blue": label_color = "#206694"
        elif label_color == "purple": label_color = "#9b59b6"
        elif label_color == "dark_purple": label_color = "#71368a"
        elif label_color == "magenta": label_color = "#e91e63"
        elif label_color == "dark_magenta": label_color = "#ad1457"
        elif label_color == "yellow": label_color = "#f5ef42"
        elif label_color == "dark_yellow": label_color = "#a6a126"
        elif label_color == "gold": label_color = "#f1c40f"
        elif label_color == "dark_gold": label_color = "#c27c0e"
        elif label_color == "orange": label_color = "#e67e22"
        elif label_color == "dark_orange": label_color = "#a84300"
        elif label_color == "red": label_color = "#e74c3c"
        elif label_color == "dark_red": label_color = "#992d22"
        elif label_color in ["lighter_gray", "lighter_grey"]: label_color = "#95a5a6"
        elif label_color in ["light_gray", "light_grey"]: label_color = "#979c9f"
        elif label_color in ["dark_gray", "dark_grey"]: label_color = "#607d8b"
        elif label_color in ["darker_gray", "darker_grey"]: label_color = "#546e7a"
        elif label_color == "blurple": label_color = "#7289da"
        elif label_color in ["grayple", "greyple"]: label_color = "#99aab5"
        elif label_color == "white": label_color = "#fffffe"
        elif label_color == "black": label_color = "#000000"
        elif label_color in ["default", "none"]: label_color = "#ffffff"
        if label_color.startswith("0x"): label_color = label_color.replace("0x", "#", 1)

        if not label_color.startswith("#"): return "Invalid preset! Make sure it's in the above list or check your spelling.", label_color.replace("#", "", 1)
        label_color = label_color.replace("#", "", 1)
        if not re.match(r"[0-9a-f]{6}$", label_color): return "Invalid hex code!", label_color
        return None, label_color
    error, label_color = validate_color(label_color)
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        label_color = await ask_message(ctx, embed)
        if label_color == None: return
        error, label_color = validate_color(label_color)

    # label_emoji
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new label... (5/5)")
    embed.add_field(name="What should the label's emoji be?", value="This is what references the label whenever the user needs to select a label for his feedback. When using a custom emoji, make sure it is from a server I am also in.")
    label_emoji = await ask_message(ctx, embed=embed)
    if label_emoji == None: return
    try: await ctx.message.add_reaction(label_emoji)
    except: error = "Couldn't use this as an emoji!"
    else: error = None
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        label_emoji = await ask_message(ctx, embed)
        if label_emoji == None: return
        try: await ctx.message.add_reaction(label_emoji)
        except: error = "Couldn't use this as an emoji!"
        else: error = None



    if validate_shortname():
        raise CustomException("Couldn't create label!", validate_shortname())

    label = models.Label.create(feed.feed_id, label_name=label_name, label_shortname=label_shortname, label_color=label_color, label_desc=label_desc, label_desc_url=label_desc_url, label_emoji=label_emoji)
    embed = discord.Embed(
        color=discord.Color(7844437),
        description=f"You can change the configuration at any time, using the below command:```{ctx.prefix}feed {feed.feed_shortname} label {label.label_shortname} <option> <new value>```\nAvailable options: name, shortname, description, color"
    )
    embed.set_author(name=f"Label \"{label_name}\" created", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    await ctx.send(embed=embed)
    await show_label(ctx, feed, label)
async def create_trigger(ctx):
    feeds = models.Guild(ctx.guild.id).feeds
    if not feeds: raise CustomException('No feeds!', 'You need to create a feed first before you can create a trigger for one.')
    # feed_id
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new trigger... (1/3)")
    embed.add_field(name="What feed should this trigger be linked to?", value=f"This is the feed feedback will be created in when triggered. Enter either a feed's short name or its index.\n\nAvailable feeds:\n{', '.join([feed.feed_shortname for feed in feeds])}")
    feed_shortname = await ask_message(ctx, embed=embed)
    if feed_shortname == None: return
    def validate_feed():
        try: models.Feed.find(ctx.guild.id, feed_shortname)
        except models.NotFound: return "Couldn't find feed!"
        else: return None
    error = validate_feed()
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        feed_shortname = await ask_message(ctx, embed)
        if feed_shortname == None: return
        error = validate_feed()
    feed_id = models.Feed.find(ctx.guild.id, feed_shortname).feed_id
    
    # trigger_emoji
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new label... (2/3)")
    embed.add_field(name="What should the trigger's emoji be?", value="This is what will be used for the reaction under the trigger message. When using a custom emoji, make sure it is from a server I am also in.")
    trigger_emoji = await ask_message(ctx, embed=embed)
    if trigger_emoji == None: return
    try: await ctx.message.add_reaction(trigger_emoji)
    except: error = "Couldn't use this as an emoji!"
    else: error = None
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        trigger_emoji = await ask_message(ctx, embed)
        if trigger_emoji == None: return
        try: await ctx.message.add_reaction(trigger_emoji)
        except: error = "Couldn't use this as an emoji!"
        else: error = None

    # trigger_message
    embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
    embed.set_author(name="Creating new label... (3/3)")
    embed.add_field(name="What message should the trigger be under?", value="This is the message that will have the reaction to trigger the trigger. Enter either the URL to a message, the channel and message ID with a dash inbetween (`<channel id>-<message id>`), or whenever it's in this channel just the message ID.")
    trigger_message = await ask_message(ctx, embed=embed)
    if trigger_message == None: return
    try:
        message = await commands.MessageConverter().convert(ctx, trigger_message)
        error = None
    except commands.BadArgument as e: error = str(e)
    while error is not None:
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
        embed.set_author(name=error)
        trigger_message = await ask_message(ctx, embed)
        if trigger_message == None: return
        try:
            message = await commands.MessageConverter().convert(ctx, trigger_message)
            error = None
        except commands.BadArgument as e: error = str(e)
    trigger_channel_id = message.channel.id
    trigger_message_id = message.id
  

    trigger = models.Trigger.create(guild_id=ctx.guild.id, feed_id=feed_id, trigger_emoji=trigger_emoji, trigger_channel_id=trigger_channel_id, trigger_message_id=trigger_message_id)
    embed = discord.Embed(
        color=discord.Color(7844437),
        description=f"You can change the configuration at any time, using the below command:```{ctx.prefix}trigger {trigger.index+1} <option> <new value>```\nAvailable options: feed, emoji, message"
    )
    embed.set_author(name=f"Trigger created", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    await ctx.send(embed=embed)
    await show_trigger(ctx, trigger)
    await message.add_reaction(trigger.trigger_emoji)

async def delete_feed(ctx, feed):
    embed = discord.Embed(color=discord.Color.gold())
    embed.add_field(name=f"⚠️ Are you sure you want to delete \"{feed.feed_name}\"?", value="This removes all feedback from the database and can not be undone.")
    options = {
        "<:yes:809149148356018256>": "Yes, __permanently__ delete the feed",
        "<:no:808045512393621585>": "No, keep the feed"
    }
    res = await ask_reaction(ctx, embed, options)
    
    if res == "<:yes:809149148356018256>":
        feed_name = feed.feed_name
        feed.delete()
        embed = discord.Embed(color=discord.Color(7844437))
        embed.set_author(name=f"Feed \"{feed_name}\" deleted", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
        await ctx.send(embed=embed)
async def delete_label(ctx, feed, label):
    embed = discord.Embed(color=discord.Color.gold())
    embed.add_field(name=f"⚠️ Are you sure you want to delete \"{label.label_name}\"?", value="This will remove the label from any feedback using it can not be undone.")
    options = {
        "<:yes:809149148356018256>": "Yes, __permanently__ delete the label",
        "<:no:808045512393621585>": "No, keep the label"
    }
    res = await ask_reaction(ctx, embed, options)
    
    if res == "<:yes:809149148356018256>":
        label_name = label.label_name
        label.delete()
        embed = discord.Embed(color=discord.Color(7844437))
        embed.set_author(name=f"Label \"{label_name}\" deleted", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
        await ctx.send(embed=embed)
async def delete_trigger(ctx, trigger):
    embed = discord.Embed(color=discord.Color.gold())
    embed.add_field(name=f"⚠️ Are you sure you want to delete this trigger?", value="This will also remove the emoji from the trigger message.")
    options = {
        "<:yes:809149148356018256>": "Yes, __permanently__ delete the trigger",
        "<:no:808045512393621585>": "No, keep the trigger"
    }
    res = await ask_reaction(ctx, embed, options)
    
    if res == "<:yes:809149148356018256>":
        try:
            message = await commands.MessageConverter().convert(ctx, f'{trigger.trigger_channel_id}-{trigger.trigger_message_id}')
            await message.clear_reaction(trigger.trigger_emoji)
        except: pass
        trigger.delete()
        embed = discord.Embed(color=discord.Color(7844437))
        embed.set_author(name=f"Trigger deleted", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
        await ctx.send(embed=embed)



async def show_feed_name(ctx, feed):
    color = discord.Color(int(feed.feed_color, 16)) if feed.feed_color else discord.Embed.Empty
    embed = discord.Embed(color=color, title="Feed Name", description="The name of the feed, should be pretty self-explanatory. May contain special characters. 20 characters max.")
    embed.set_author(name=feed.feed_name)
    embed.add_field(name="Current value:", value=feed.feed_name, inline=False)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}feed {feed.feed_shortname} name <new value>```", inline=False)
    await ctx.send(embed=embed)
async def show_feed_shortname(ctx, feed):
    color = discord.Color(int(feed.feed_color, 16)) if feed.feed_color else discord.Embed.Empty
    embed = discord.Embed(color=color, title="Feed Short Name", description="The short name of the feed, also known as the identifier. This is a short word used to reference the feed in a command. Short names may not use capitalization, spaces or special characters. Only alphabetical characters, digits, underscores, and dashes. You can't have identical identifiers within one guild.")
    embed.set_author(name=feed.feed_name)
    embed.add_field(name="Current value:", value="`"+feed.feed_shortname+"`", inline=False)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}feed {feed.feed_shortname} shortname <new value>```", inline=False)
    await ctx.send(embed=embed)
async def show_feed_desc(ctx, feed):
    color = discord.Color(int(feed.feed_color, 16)) if feed.feed_color else discord.Embed.Empty
    embed = discord.Embed(color=color, title="Feed Description", description="The description of your feed. This is the first thing shown to the user whenever creating feedback. You can include __all__ *sorts* `of` **formatting**, including [hyperlinks](https://support.discord.com/hc/en-us/articles/210298617-Markdown-Text-101-Chat-Formatting-Bold-Italic-Underline-). 1500 characters max. You can also upload an image file, which will be displayed below the description.\n\nFormatting example:```\nItalics: *text* or _text_\nBold: **text**\nUnderlined: __text__\nStrikethrough: ~~text~~\nQuoted line: > text\nQuoted paragraph: >>> text\nHyperlink: [text](url)\nIn-line code: `text`\nCode block: `‏``text``‏`\n```")
    embed.set_author(name=feed.feed_name)
    embed.add_field(name="Current value:", value=feed.feed_desc, inline=False)
    if feed.feed_desc_url: embed.set_image(url=feed.feed_desc_url)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}feed {feed.feed_shortname} description <new value>```", inline=False)
    await ctx.send(embed=embed)
async def show_feed_color(ctx, feed):
    color = discord.Color(int(feed.feed_color, 16)) if feed.feed_color else discord.Embed.Empty
    embed = discord.Embed(color=color, title="Feed Color", description="The default color feedback in this feed will be labeled with. This can be overwritten by labels. This needs to be [a color hex code](https://htmlcolorcodes.com/color-picker/), for instance `#f82ea1`. You can also pick one of the presets, or type \"default\" for no color.\n\nAvailable presets:\nteal, dark_teal, green, dark_green, blue, dark_blue, purple, dark_purple, magenta, dark_magenta, yellow, dark_yellow, gold, dark_gold, orange, dark_orange, red, dark_red, lighter_gray, light_gray, dark_gray, darker_gray, blurple, grayple, white, black")
    embed.set_author(name=feed.feed_name)
    embed.add_field(name="Current value:", value="#"+feed.feed_color, inline=False)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}feed {feed.feed_shortname} color <new value>```", inline=False)
    await ctx.send(embed=embed)
async def show_feed_channel(ctx, feed):
    color = discord.Color(int(feed.feed_color, 16)) if feed.feed_color else discord.Embed.Empty
    embed = discord.Embed(color=color, title="Feed Channel", description="The name of the feed, should be pretty self-explanatory. May contain special characters. 20 characters max.")
    embed.set_author(name=feed.feed_name)
    channel = ctx.guild.get_channel(feed.feed_channel_id)
    channel = channel.mention if channel else "No channel ⚠️"
    embed.add_field(name="Current value:", value=channel, inline=False)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}feed {feed.feed_shortname} channel <new value>```", inline=False)
    await ctx.send(embed=embed)
async def show_feed_anonymous(ctx, feed):
    color = discord.Color(int(feed.feed_color, 16)) if feed.feed_color else discord.Embed.Empty
    embed = discord.Embed(color=color, title="Feed Anonymous", description="Whether new feedback should hide the user who submitted it. Accepts either 0 (= show user) or 1 (= hide user).")
    embed.set_author(name=feed.feed_name)
    embed.add_field(name="Current value:", value=str(feed.anonymous), inline=False)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}feed {feed.feed_shortname} anonymous <new value>```", inline=False)
    await ctx.send(embed=embed)
async def show_feed_reactions(ctx, feed):
    color = discord.Color(int(feed.feed_color, 16)) if feed.feed_color else discord.Embed.Empty
    embed = discord.Embed(color=color, title="Feed Reactions", description="If and what reactions should be added to new feedback. Accepts a list of emojis, separated by commas. The bot must have access to the emojis, so either a default emoji or one from a server the bot is in too. You can also type \"none\", for no reactions.")
    embed.set_author(name=feed.feed_name)
    embed.add_field(name="Current value:", value=feed.reactions, inline=False)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}feed {feed.feed_shortname} reactions <new value>```", inline=False)
    await ctx.send(embed=embed)


async def set_feed_name(ctx, feed, value):
    if len(value) > 20: raise CustomException("Invalid length!", f"You may only use 20 characters max, you have {len(value)}.")

    embed = discord.Embed(color=discord.Color(7844437))
    embed.set_footer(text=f"Feed: {feed.feed_name} - ID: {feed.feed_shortname}")
    embed.set_author(name="Feed name updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=feed.feed_name)
    embed.add_field(name="New value", value=value)
    
    feed.feed_name = value
    feed.save()
    
    await ctx.send(embed=embed)
async def set_feed_shortname(ctx, feed, value):
    if len(value) > 20: raise CustomException("Invalid length!", f"You may only use 20 characters max, you have {len(value)}.")
    if not re.match(r"[a-zA-Z0-9_-]+$", value): raise CustomException("Invalid character(s)!", "You can only use [a-z0-9_-].")
    try: int(value)
    except ValueError: pass
    else: raise CustomException("Invalid short name!", "Your name can't fully consist of numbers.")
    try: models.Feed.find(ctx.guild.id, value)
    except models.NotFound: pass
    else: raise CustomException("Invalid short name!", "A feed with this short name already exists.")

    embed = discord.Embed(color=discord.Color(7844437))
    embed.set_footer(text=f"Feed: {feed.feed_name} - ID: {feed.feed_shortname}")
    embed.set_author(name="Feed short name updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=feed.feed_shortname)
    embed.add_field(name="New value", value=value)
    
    feed.feed_shortname = value
    feed.save()
    
    await ctx.send(embed=embed)
async def set_feed_desc(ctx, feed, value):
    if len(value) > 1500: raise CustomException("Invalid description!", f"You may only use 1500 characters max, you have {len(value)}.")
    image = ""
    for attachment in ctx.message.attachments:
        if attachment.height:
            image = attachment.url
            break

    embed = discord.Embed(color=discord.Color(7844437))
    embed.set_footer(text=f"Feed: {feed.feed_name} - ID: {feed.feed_shortname}")
    embed.set_author(name="Feed description updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=feed.feed_desc if len(feed.feed_desc) <= 1024 else feed.feed_desc[:1022]+"..", inline=False)
    embed.add_field(name="New value", value=value if len(value) <= 1024 else value[:1022]+"..", inline=False)
    if image: embed.set_image(url=image)

    feed.feed_desc = value
    feed.feed_desc_url = image
    feed.save()
    
    await ctx.send(embed=embed)
async def set_feed_color(ctx, feed, value):
    value = value.lower()
    if value == "teal": value = "#1abc9c"
    elif value == "dark_teal": value = "#11806a"
    elif value == "green": value = "#2ecc71"
    elif value == "dark_green": value = "#1f8b4c"
    elif value == "blue": value = "#3498db"
    elif value == "dark_blue": value = "#206694"
    elif value == "purple": value = "#9b59b6"
    elif value == "dark_purple": value = "#71368a"
    elif value == "magenta": value = "#e91e63"
    elif value == "dark_magenta": value = "#ad1457"
    elif value == "yellow": value = "#f5ef42"
    elif value == "dark_yellow": value = "#a6a126"
    elif value == "gold": value = "#f1c40f"
    elif value == "dark_gold": value = "#c27c0e"
    elif value == "orange": value = "#e67e22"
    elif value == "dark_orange": value = "#a84300"
    elif value == "red": value = "#e74c3c"
    elif value == "dark_red": value = "#992d22"
    elif value in ["lighter_gray", "lighter_grey"]: value = "#95a5a6"
    elif value in ["light_gray", "light_grey"]: value = "#979c9f"
    elif value in ["dark_gray", "dark_grey"]: value = "#607d8b"
    elif value in ["darker_gray", "darker_grey"]: value = "#546e7a"
    elif value == "blurple": value = "#7289da"
    elif value in ["grayple", "greyple"]: value = "#99aab5"
    elif value == "white": value = "#fffffe"
    elif value == "black": value = "#000000"
    elif value in ["default", "none"]: value = "#ffffff"
    if value.startswith("0x"): value = value.replace("0x", "#", 1)

    if not value.startswith("#"): raise CustomException("Invalid color!", f"No preset with name \"{value}\" could be found.")
    value = value.replace("#", "", 1)
    if not re.match(r"[0-9a-f]{6}$", value): raise CustomException("Invalid color!", "No color matches this hex code.")

    embed = discord.Embed(color=discord.Color(int(value, 16)))
    embed.set_author(name="Feed color updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=f"#{feed.feed_color}")
    embed.add_field(name="New value", value=f"#{value}")

    feed.feed_color = value
    feed.save()
    
    await ctx.send(embed=embed)
async def set_feed_channel(ctx, feed, value):
    converter = commands.TextChannelConverter()
    try: channel = await converter.convert(ctx, value)
    except commands.BadArgument as e: raise CustomException("Invalid channel!", str(e))

    try: old_channel = (await converter.convert(ctx, feed.feed_channel_id)).mention
    except commands.BadArgument: old_channel = "No channel"

    embed = discord.Embed(color=discord.Color(7844437))
    embed.set_footer(text=f"Feed: {feed.feed_name} - ID: {feed.feed_shortname}")
    embed.set_author(name="Feed channel updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=old_channel)
    embed.add_field(name="New value", value=channel.mention)
    
    feed.feed_channel = channel.id
    feed.save()
    
    await ctx.send(embed=embed)
async def set_feed_anonymous(ctx, feed, value):
    if str(value) != "0" and str(value) != "1":
        raise CustomException("Invalid value!", f"Type either \"0\" or \"1\".")
    value = int(value)

    embed = discord.Embed(color=discord.Color(7844437))
    embed.set_footer(text=f"Feed: {feed.feed_name} - ID: {feed.feed_shortname}")
    if value == 1: embed.set_author(name="Feed will now be anonymous", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    else: embed.set_author(name="Feed will now no longer be anonymous", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    
    feed.anonymous = value
    feed.save()
    
    await ctx.send(embed=embed)
async def set_feed_reactions(ctx, feed, value):
    if value.lower() == "none":
        value = ""
    else:
        emojis = [emoji.strip() for emoji in value.split(',')]
        converter = commands.EmojiConverter()
        with open('emoji_map.json', 'r') as f:
            emoji_map = json.load(f)
        for emoji in emojis:
            if emoji not in emoji_map.values():
                try: await converter.convert(ctx, emoji)
                except commands.BadArgument: raise CustomException('Invalid emoji!', f"Can't recognize \"{emoji}\" as an emoji.")
        value = ",".join(emojis)

    embed = discord.Embed(color=discord.Color(7844437))
    embed.set_footer(text=f"Feed: {feed.feed_name} - ID: {feed.feed_shortname}")
    if value: embed.set_author(name="Feed reactions updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    else: embed.set_author(name="Feed will now no longer show reactions", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=feed.reactions if feed.reactions else 'None')
    embed.add_field(name="New value", value=value)

    feed.reactions = value
    feed.save()
    
    await ctx.send(embed=embed)


async def show_label_name(ctx, feed, label):
    color = discord.Color(int(label.label_color, 16)) if label.label_color else discord.Embed.Empty
    embed = discord.Embed(color=color, title="Label Name", description="The name of the label, should be pretty self-explanatory. May contain special characters. 20 characters max.")
    embed.set_author(name=label.label_name)
    embed.add_field(name="Current value:", value=label.label_name, inline=False)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}label {label.label_shortname} name <new value>```", inline=False)
    await ctx.send(embed=embed)
async def show_label_shortname(ctx, feed, label):
    color = discord.Color(int(label.label_color, 16)) if label.label_color else discord.Embed.Empty
    embed = discord.Embed(color=color, title="Label Short Name", description="The short name of the label, also known as the identifier. This is a short word used to reference the label in a command. Short names may not use capitalization, spaces or special characters. Only alphabetical characters, digits, underscores, and dashes. You can't have identical identifiers within one guild.")
    embed.set_author(name=label.label_name)
    embed.add_field(name="Current value:", value="`"+label.label_shortname+"`", inline=False)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}label {label.label_shortname} shortname <new value>```", inline=False)
    await ctx.send(embed=embed)
async def show_label_desc(ctx, feed, label):
    color = discord.Color(int(label.label_color, 16)) if label.label_color else discord.Embed.Empty
    embed = discord.Embed(color=color, title="Label Description", description="The description of your label. This is appended to the standard description of the feed. You can include __all__ *sorts* `of` **formatting**, including [hyperlinks](https://support.discord.com/hc/en-us/articles/210298617-Markdown-Text-101-Chat-Formatting-Bold-Italic-Underline-). 1500 characters max. You can also upload an image file, which will be displayed below the description.\n\nFormatting example:```\nItalics: *text* or _text_\nBold: **text**\nUnderlined: __text__\nStrikethrough: ~~text~~\nQuoted line: > text\nQuoted paragraph: >>> text\nHyperlink: [text](url)\nIn-line code: `text`\nCode block: `‏``text``‏`\n```")
    embed.set_author(name=label.label_name)
    embed.add_field(name="Current value:", value=label.label_desc, inline=False)
    if label.label_desc_url: embed.set_image(url=label.label_desc_url)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}label {label.label_shortname} description <new value>```", inline=False)
    await ctx.send(embed=embed)
async def show_label_color(ctx, feed, label):
    color = discord.Color(int(label.label_color, 16)) if label.label_color else discord.Embed.Empty
    embed = discord.Embed(color=color, title="Label Color", description="The color any feedback with this label will have. This will overwrite the default color of the feed, if any. This needs to be [a color hex code](https://htmlcolorcodes.com/color-picker/), for instance `#f82ea1`. You can also pick one of the presets, or type \"default\" for no color.\n\nAvailable presets:\nteal, dark_teal, green, dark_green, blue, dark_blue, purple, dark_purple, magenta, dark_magenta, yellow, dark_yellow, gold, dark_gold, orange, dark_orange, red, dark_red, lighter_gray, light_gray, dark_gray, darker_gray, blurple, grayple, white, black")
    embed.set_author(name=label.label_name)
    embed.add_field(name="Current value:", value="#"+label.label_color, inline=False)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}label {label.label_shortname} color <new value>```", inline=False)
    await ctx.send(embed=embed)
async def show_label_emoji(ctx, feed, label):
    color = discord.Color(int(label.label_color, 16)) if label.label_color else discord.Embed.Empty
    embed = discord.Embed(color=color, title="Label Emoji", description="The emoji users will have to select when choosing a label for their feedback. This needs to be a single emoji that the bot has access to, so either a default emoji or one from a server the bot is in, this one for instance!")
    embed.set_author(name=label.label_name)
    embed.add_field(name="Current value:", value=label.label_emoji, inline=False)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}label {label.label_shortname} emoji <new value>```", inline=False)
    await ctx.send(embed=embed)

async def set_label_name(ctx, feed, label, value):
    if len(value) > 20: raise CustomException("Invalid length!", f"You may only use 20 characters max, you have {len(value)}.")

    embed = discord.Embed(color=discord.Color(7844437))
    embed.set_footer(text=f"Feed: {label.label_name} - ID: {label.label_shortname}")
    embed.set_author(name="Label name updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=label.label_name)
    embed.add_field(name="New value", value=value)
    
    label.label_name = value
    label.save()
    
    await ctx.send(embed=embed)
async def set_label_shortname(ctx, feed, label, value):
    if len(value) > 20: raise CustomException("Invalid length!", f"You may only use 20 characters max, you have {len(value)}.")
    if not re.match(r"[a-zA-Z0-9_-]+$", value): raise CustomException("Invalid character(s)!", "You can only use [a-z0-9_-].")
    try: int(value)
    except ValueError: pass
    else: raise CustomException("Invalid short name!", "Your name can't fully consist of numbers.")
    try: models.Label.find(ctx.guild.id, value)
    except models.NotFound: pass
    else: raise CustomException("Invalid short name!", "A label with this short name already exists.")

    embed = discord.Embed(color=discord.Color(7844437))
    embed.set_footer(text=f"Feed: {label.label_name} - ID: {label.label_shortname}")
    embed.set_author(name="Label short name updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=label.label_shortname)
    embed.add_field(name="New value", value=value)
    
    label.label_shortname = value
    label.save()
    
    await ctx.send(embed=embed)
async def set_label_desc(ctx, feed, label, value):
    if len(value) > 1500: raise CustomException("Invalid description!", f"You may only use 1500 characters max, you have {len(value)}.")
    image = ""
    for attachment in ctx.message.attachments:
        if attachment.height:
            image = attachment.url
            break

    embed = discord.Embed(color=discord.Color(7844437))
    embed.set_footer(text=f"Feed: {label.label_name} - ID: {label.label_shortname}")
    embed.set_author(name="Label description updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=label.label_desc if len(label.label_desc) <= 1024 else label.label_desc[:1022]+"..", inline=False)
    embed.add_field(name="New value", value=value if len(value) <= 1024 else value[:1022]+"..", inline=False)
    if image: embed.set_image(url=image)

    label.label_desc = value
    label.label_desc_url = image
    label.save()
    
    await ctx.send(embed=embed)
async def set_label_color(ctx, feed, label, value):
    value = value.lower()
    if value == "teal": value = "#1abc9c"
    elif value == "dark_teal": value = "#11806a"
    elif value == "green": value = "#2ecc71"
    elif value == "dark_green": value = "#1f8b4c"
    elif value == "blue": value = "#3498db"
    elif value == "dark_blue": value = "#206694"
    elif value == "purple": value = "#9b59b6"
    elif value == "dark_purple": value = "#71368a"
    elif value == "magenta": value = "#e91e63"
    elif value == "dark_magenta": value = "#ad1457"
    elif feed_color == "yellow": feed_color = "#f5ef42"
    elif feed_color == "dark_yellow": feed_color = "#a6a126"
    elif value == "gold": value = "#f1c40f"
    elif value == "dark_gold": value = "#c27c0e"
    elif value == "orange": value = "#e67e22"
    elif value == "dark_orange": value = "#a84300"
    elif value == "red": value = "#e74c3c"
    elif value == "dark_red": value = "#992d22"
    elif value in ["lighter_gray", "lighter_grey"]: value = "#95a5a6"
    elif value in ["light_gray", "light_grey"]: value = "#979c9f"
    elif value in ["dark_gray", "dark_grey"]: value = "#607d8b"
    elif value in ["darker_gray", "darker_grey"]: value = "#546e7a"
    elif value == "blurple": value = "#7289da"
    elif value in ["grayple", "greyple"]: value = "#99aab5"
    elif value == "white": value = "#fffffe"
    elif value == "black": value = "#000000"
    elif value in ["default", "none"]: value = "#ffffff"
    if value.startswith("0x"): value = value.replace("0x", "#", 1)

    if not value.startswith("#"): raise CustomException("Invalid color!", f"No prefix with name \"{value}\" could be found.")
    value = value.replace("#", "", 1)
    if not re.match(r"[0-9a-f]{6}$", value): raise CustomException("Invalid color!", "No color matches this hex code.")

    embed = discord.Embed(color=discord.Color(int(value, 16)))
    embed.set_author(name="Label color updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=f"#{label.label_color}")
    embed.add_field(name="New value", value=f"#{value}")

    label.label_color = value
    label.save()
    
    await ctx.send(embed=embed)
async def set_label_emoji(ctx, feed, label, value):
    try: await ctx.message.add_reaction(value)
    except: raise CustomException('Invalid emoji!', 'Couldn\'t react to a message using emoji "%s"' % value)

    embed = discord.Embed(color=discord.Color(7844437))
    embed.set_footer(text=f"Feed: {label.label_name} - ID: {label.label_shortname}")
    embed.set_author(name="Label emoji updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=label.label_emoji)
    embed.add_field(name="New value", value=value)
    
    label.label_emoji = value
    label.save()
    
    await ctx.send(embed=embed)


async def show_trigger_feed(ctx, trigger):
    embed = discord.Embed(title="Trigger Feed", description=f"The feed this trigger creates feedback for when triggered. Should be either the feed's short name or index. See `{ctx.prefix}feeds`.")
    embed.add_field(name="Current value:", value=trigger.feed.feed_shortname, inline=False)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}trigger {trigger.index+1} feed <new value>```", inline=False)
    await ctx.send(embed=embed)
async def show_trigger_emoji(ctx, trigger):
    embed = discord.Embed(title="Trigger Emoji", description="The emoji that is added to the trigger message that users will have to react with. When using a custom emoji, make sure it is from a server I am also in.")
    embed.add_field(name="Current value:", value=trigger.trigger_emoji, inline=False)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}trigger {trigger.index+1} feed <new value>```", inline=False)
    await ctx.send(embed=embed)
async def show_trigger_message(ctx, trigger):
    try: message = await commands.MessageConverter().convert(ctx, f'{trigger.trigger_channel_id}-{trigger.trigger_message_id}')
    except commands.BadArgument: message = None
    if message: jump = message.jump_url
    else: jump = "No message ⚠️"
    embed = discord.Embed(title="Trigger Message", description="The feed this trigger creates feedback for when triggered. Should be either the URL to a message, the channel and message ID with a dash inbetween (`<channel id>-<message id>`), or whenever it's in this channel just the message ID.")
    embed.add_field(name="Current value:", value=jump, inline=False)
    embed.add_field(name="To change it:", value=f"```{ctx.prefix}trigger {trigger.index+1} message <new value>```", inline=False)
    await ctx.send(embed=embed)

async def set_trigger_feed(ctx, trigger, value):
    feed = models.Feed.find(ctx.guild.id, value)

    embed = discord.Embed(color=discord.Color(7844437))
    embed.set_author(name="Trigger feed updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=trigger.feed.feed_shortname)
    embed.add_field(name="New value", value=feed.feed_shortname)
    
    trigger.feed_id = feed.feed_id
    trigger.save()
    
    await ctx.send(embed=embed)
async def set_trigger_emoji(ctx, trigger, value):
    try:
        message = await commands.MessageConverter().convert(ctx, f"{trigger.trigger_channel_id}-{trigger.trigger_message_id}")
        await message.remove_reaction(trigger.trigger_emoji, ctx.guild.me)
    except: message = ctx.message
    try: await message.add_reaction(value)
    except: raise CustomException("Invalid emoji!", "Couldn't use this as an emoji.")

    embed = discord.Embed(color=discord.Color(7844437))
    embed.set_author(name="Trigger emoji updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=trigger.trigger_emoji)
    embed.add_field(name="New value", value=value)

    trigger.trigger_emoji = value
    trigger.save()
    
    await ctx.send(embed=embed)
async def set_trigger_message(ctx, trigger, value):
    try: message = await commands.MessageConverter().convert(ctx, value)
    except commands.BadArgument as e: raise CustomException('Invalid message!', str(e))

    try:
        message_old = await commands.MessageConverter().convert(ctx, f"{trigger.trigger_channel_id}-{trigger.trigger_message_id}")
        jump_old = message_old.jump_url
    except commands.BadArgument:
        message_old = None
        jump_old = "No message ⚠️"

    embed = discord.Embed(color=discord.Color(7844437))
    embed.set_author(name="Trigger message updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
    embed.add_field(name="Old value", value=jump_old)
    embed.add_field(name="New value", value=message.jump_url)
    
    trigger.trigger_channel_id = message.channel.id
    trigger.trigger_message_id = message.id
    trigger.save()

    if message_old: await message_old.clear_reaction(trigger.trigger_emoji)
    await message.add_reaction(trigger.trigger_emoji)
    
    await ctx.send(embed=embed)



async def show_feedback(ctx, feed, feedback):
    label = feedback.label
    if label:
        color = discord.Color(int(label.label_color, 16))
        title = f"#{feedback.feedback_id} | {feed.feed_name} ({label.label_name})"
    else:
        color = discord.Color(int(feed.feed_color, 16))
        title = f"#{feedback.feedback_id} | {feed.feed_name}"

    embed = discord.Embed(color=color, title=title, description=feedback.feedback_desc)
    author = ctx.guild.get_member(feedback.feedback_author)
    if author: embed.set_author(icon_url=author.avatar_url, name=str(author))
    else: embed.set_author(name="⚠️ The author has left the server")
    embed.add_field(name='Author', value=feedback.feedback_author)
    embed.add_field(name='Feed', value=feed.feed_name)
    embed.add_field(name='Label', value=label.label_name if label else "None")

    message = None
    channel = ctx.guild.get_channel(feedback.channel_id)
    if channel: message = await channel.fetch_message(feedback.message_id)

    if feed.reactions:
        if message:
            emojis = feed.reactions.split(',')
            reactions = dict()
            for emoji in emojis:
                reactions[emoji] = 0
            for reaction in message.reactions:
                emoji = str(reaction.emoji)
                if emoji in emojis:
                    if ctx.bot.user in (await reaction.users().flatten()): reactions[emoji] = reaction.count - 1
                    else: reactions[emoji] = reaction.count
            embed.add_field(name='Reactions', value=", ".join([f'{k} **{v}**' for k, v in reactions.items()]), inline=False)
        else:
            embed.add_field(name='Reactions', value="Could no longer find message", inline=False)

    if message: embed.add_field(name='‏', value=f"[[Jump to message]]({message.jump_url})", inline=False)
    if feedback.feedback_desc_url: embed.set_image(url=feedback.feedback_desc_url)
    await ctx.send(embed=embed)
async def create_feedback(ctx, feed):
    # Does feed channel still exist?
    feed_channel = ctx.guild.get_channel(feed.feed_channel_id)
    if not feed_channel: raise CustomException("Can't create feedback!", "No channel to send feedback to was set")

    # Is user already creating feedback?
    feedback = models.has_unfinished_feedback(ctx.guild.id, ctx.author.id)
    if feedback:
        channel = ctx.guild.get_channel(feedback.creation_channel_id)
        if not channel:
            feedback.delete()
        else:
            await channel.send(f"{ctx.author.mention}, finish or close this first before attempting to create more!")
            return            

    # Create channel
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.guild.me: discord.PermissionOverwrite.from_pair(allow=[(k, v) for k, v in discord.Permissions.all()], deny=[]),
        ctx.author: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=False, send_tts_messages=True, attach_files=True, external_emojis=True)
    }
    guild = models.Guild(ctx.guild.id)
    if guild.mod_role:
        mod_role = ctx.guild.get_role(guild.mod_role)
        if mod_role: overwrites[mod_role] = discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True, send_tts_messages=True, attach_files=True, external_emojis=True)
    if guild.admin_role and guild.admin_role != guild.mod_role:
        admin_role = ctx.guild.get_role(guild.admin_role)
        if admin_role: overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True, send_tts_messages=True, attach_files=True, external_emojis=True)

    try: channel = await feed_channel.category.create_text_channel(f"{feed.feed_name} {ctx.author.name}", overwrites=overwrites)
    except: raise CustomException("I don't have permission!", "Contact a server admin to give me Manage Channels and Manage Roles perms.")
    message = await channel.send(f"{ctx.author.mention} create your feedback here!")
    feedback = models.Feedback.new(feed_id=feed.feed_id, feedback_author=ctx.author.id, creation_channel_id=channel.id)

    ### LABEL

    embed = discord.Embed(color=discord.Color(int(feed.feed_color, 16)))
    embed.description = feed.feed_desc
    if feed.feed_desc_url: embed.set_image(url=feed.feed_desc_url)

    def check_reaction(reaction, user):
        return reaction.message == message and not user.bot
    def check_message(message):
        return message.channel == channel and message.content and not message.author.bot

    labels = feed.labels
    if labels:
        embed.set_author(icon_url=ctx.guild.icon_url, name="Creating new feedback... (1/3)")
        embed.set_footer(text="Want to cancel this? React with X under this message.")
        embed.description += "\n\n**First, select a label by reacting to this message.**"
        for label in labels:
            embed.description += f"\n{label.label_emoji} {label.label_name}"
        await message.edit(content="", embed=embed)
        await message.add_reaction("<:no:808045512393621585>")
        emojis = []
        for label in labels:
            emojis.append(str(label.label_emoji))
            try: await message.add_reaction(label.label_emoji)
            except: await ctx.send(f"<:no:808045512393621585> Couldn't add label {label.label_name}, contact a server admin.")

        res = ""
        while res not in emojis:
            reaction, user = await ctx.bot.wait_for('reaction_add', check=check_reaction)
            if str(reaction.emoji) == "<:no:808045512393621585>":
                feedback.delete()
                await channel.delete()
                return
            else:
                emoji = str(reaction.emoji)
                await message.remove_reaction(emoji, user)
                if not user.bot and emoji in emojis:
                    res = emoji
                    try: label = models.Label(options={'label_emoji': emoji})
                    except models.NotFound: res = ""
        
        feedback.label_id = label.label_id
        await message.clear_reactions()

        embed = discord.Embed(color=discord.Color(int(label.label_color, 16)))
        embed.set_author(icon_url=ctx.guild.icon_url, name="Creating new feedback... (2/3)")
        embed.set_footer(text="Want to cancel this? Type \"cancel\" as your response.")
        embed.description = feed.feed_desc
        if label.label_desc_url: embed.set_image(url=label.label_desc_url)
        elif feed.feed_desc_url: embed.set_image(url=feed.feed_desc_url)

        embed.description += f"\n\n{label.label_desc}"
        embed.description += "\n\n**Now, type out your actual feedback below.**"
        if len(embed.description) > 2048:
            embed.description = embed.description[:2046] + ".."
            await channel.send("⚠️ Feed and label description together are longer than 2048 characters and had to be stripped.")

        await message.edit(embed=embed)       
        
    else:
        label = None
        embed.set_author(icon_url=ctx.guild.icon_url, name="Creating new feedback... (1/2)")
        embed.set_footer(text="Want to cancel this? Type \"cancel\" as your response.")
        embed.description += "\n\n**Type out your feedback below.**"
        await message.edit(content="", embed=embed)

    
    while not feedback.finished:

        ### DESCRIPTION

        await channel.set_permissions(ctx.author, send_messages=True, view_channel=True, read_message_history=True, send_tts_messages=True, attach_files=True, external_emojis=True)

        res = None
        while not res:
            res = await ctx.bot.wait_for('message', check=check_message)
            if res.content.lower() == "cancel":
                feedback.delete()
                await channel.delete()
                return
            if res.author != ctx.author:
                res = None

        feedback.feedback_desc = res.content
        feedback.feedback_desc_url = ""
        for att in res.attachments:
            if att.height:
                if att.filename.lower().split('.')[-1] in ["tif", "tiff", "bmp", "jpg", "jpeg", "gif", "png", "eps"]:
                    feedback.feedback_desc_url = att.url
                else:
                    if att.is_spoiler: feedback.feedback_desc += f"\n\n||{att.url}||"
                    else: feedback.feedback_desc += f"\n\n{att.url}"
                break
        
        ### CONFIRMATION

        await channel.set_permissions(ctx.author, send_messages=False, view_channel=True, read_message_history=True, send_tts_messages=True, attach_files=True, external_emojis=True)
        
        if label:
            color = discord.Color(int(label.label_color, 16))
            title = f"#{feedback.feedback_id} | {feed.feed_name} ({label.label_name})"
        else:
            color = discord.Color(int(feed.feed_color, 16))
            title = f"#{feedback.feedback_id} | {feed.feed_name}"

        embed = discord.Embed(color=color, title=title, description=feedback.feedback_desc)
        embed.set_footer(text="https://github.com/timraay/FeedbackBot")
        if feedback.feedback_desc_url: embed.set_image(url=feedback.feedback_desc_url)
        if not feed.anonymous: embed.set_author(icon_url=ctx.author.avatar_url, name=str(ctx.author))
        message = await channel.send(f"Confirm that this is what you want your feedback to look like before sending. ({'3/3' if label else '2/2'})\nReact with <:yes:809149148356018256> to send your feedback, or <:no:808045512393621585> to edit it.", embed=embed)
        
        emojis = ["<:yes:809149148356018256>", "<:no:808045512393621585>"]
        for emoji in emojis:
            await message.add_reaction(emoji)
        res = ""
        while res not in emojis:
            reaction, user = await ctx.bot.wait_for('reaction_add', check=check_reaction)
            emoji = str(reaction.emoji)
            await message.remove_reaction(emoji, user)
            if not user.bot and emoji in emojis:
                res = emoji
        
        await message.clear_reactions()
        if emoji == "<:yes:809149148356018256>":
            embed.set_footer()
            sent = await feed_channel.send(embed=embed)
            
            feedback.finished = 1
            feedback.channel_id = sent.channel.id
            feedback.message_id = sent.id
            feedback.save()

            await channel.delete()

            for emoji in feed.reactions.split(','):
                if emoji:
                    try: await sent.add_reaction(emoji)
                    except: pass
        elif emoji == "<:no:808045512393621585>":
            embed = discord.Embed(color=discord.Color(int(feed.feed_color, 16)))
            embed.set_author(icon_url=ctx.guild.icon_url, name="Creating new feedback... (2/3)")
            embed.set_footer(text="Want to cancel this? Type \"cancel\" as your response.")
            embed.description = feed.feed_desc
            if label:
                if label.label_desc_url: embed.set_image(url=label.label_desc_url)
                elif feed.feed_desc_url: embed.set_image(url=feed.feed_desc_url)
            elif feed.feed_desc_url: embed.set_image(url=feed.feed_desc_url)

            if label:
                embed.color = discord.Color(int(label.label_color, 16))
                embed.description += f"\n\n{label.label_desc}"
                embed.description += "\n\n**Type out your feedback below.**"
                if len(embed.description) > 2048:
                    embed.description = embed.description[:2046] + ".."
                    await channel.send("⚠️ Feed and label description together are longer than 2048 characters and had to be stripped.")
            else:
                embed.description += "\n\n**Type out your feedback below.**"
            await message.edit(content="", embed=embed)
async def delete_feedback(ctx, feed, feedback):
    embed = discord.Embed(color=discord.Color.gold())
    name = f"{feed.feed_name} #{feedback.feedback_id}"
    embed.add_field(name=f"⚠️ Are you sure you want to delete feedback \"{name}\"?", value="This can not be undone.")
    options = {
        "<:yes:809149148356018256>": "Yes, __permanently__ delete the feedback",
        "<:no:808045512393621585>": "No, keep the feedback"
    }
    res = await ask_reaction(ctx, embed, options)
    
    if res == "<:yes:809149148356018256>":
        feedback.delete()
        try:
            message = await commands.MessageConverter().convert(ctx, f'{feedback.channel_id}-{feedback.message_id}')
            await message.delete()
        except:
            pass
        embed = discord.Embed(color=discord.Color(7844437))
        embed.set_author(name=f"Feedback \"{name}\" deleted", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
        await ctx.send(embed=embed)
