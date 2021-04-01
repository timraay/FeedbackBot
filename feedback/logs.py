import discord
from discord.utils import escape_markdown

async def log_create_action(ctx, feedback):
    feed = feedback.feed
    guild = feed.guild
    log_channel = ctx.guild.get_channel(guild.log_channel)
    if not log_channel: return

    label = feedback.label
    channel = ctx.guild.get_channel(feedback.channel_id)
    message = await channel.fetch_message(feedback.message_id)

    embed = discord.Embed(color=discord.Color.green())
    embed.set_author(icon_url=ctx.author.avatar_url, name="Feedback created")
    embed.description = feedback.feedback_desc if len(feedback.feedback_desc) <= 500 else feedback.feedback_desc[:498] + ".."
    embed.add_field(name='Details', value=f"> ID: **#{feedback.feedback_id}**\n> Feed: **{feed.feed_name}**\n> Label: **{label.label_name if label else 'None'}**")
    embed.add_field(name='Author', value=f"> Name: **{escape_markdown(ctx.author.name)}#{ctx.author.discriminator}**\n> ID: **{ctx.author.id}**\n> Mention: {ctx.author.mention}")
    embed.add_field(name='Message', value=f"> In {channel.mention}\n> [Jump to Message]({message.jump_url})")

    await log_channel.send(embed=embed)

async def log_edit_action(ctx, feedback, old_desc):
    feed = feedback.feed
    guild = feed.guild
    log_channel = ctx.guild.get_channel(guild.log_channel)
    if not log_channel: return

    label = feedback.label
    channel = ctx.guild.get_channel(feedback.channel_id)
    message = await channel.fetch_message(feedback.message_id)

    embed = discord.Embed(color=discord.Color.gold())
    embed.set_author(icon_url=ctx.author.avatar_url, name="Feedback edited")
    embed.add_field(name='Old', value=old_desc if len(old_desc) <= 1024 else old_desc[:1022] + "..", inline=False)
    embed.add_field(name='New', value=feedback.feedback_desc if len(feedback.feedback_desc) <= 1024 else feedback.feedback_desc[:1022] + "..", inline=False)
    embed.add_field(name='Details', value=f"> ID: **#{feedback.feedback_id}**\n> Feed: **{feed.feed_name}**\n> Label: **{label.label_name if label else 'None'}**")
    embed.add_field(name='Editor', value=f"> Name: **{escape_markdown(ctx.author.name)}#{ctx.author.discriminator}**\n> ID: **{ctx.author.id}**\n> Mention: {ctx.author.mention}")
    embed.add_field(name='Message', value=f"> In {channel.mention}\n> [Jump to Message]({message.jump_url})")

    await log_channel.send(embed=embed)

async def log_delete_action(ctx, feedback):
    feed = feedback.feed
    guild = feed.guild
    log_channel = ctx.guild.get_channel(guild.log_channel)
    if not log_channel: return

    label = feedback.label
    channel = ctx.guild.get_channel(feedback.channel_id)
    author = ctx.bot.get_user(feedback.feedback_author)

    embed = discord.Embed(color=discord.Color.dark_red())
    embed.set_author(icon_url=ctx.author.avatar_url, name="Feedback deleted")
    embed.description = feedback.feedback_desc if len(feedback.feedback_desc) <= 1024 else feedback.feedback_desc[:1022] + ".."
    embed.add_field(name='Details', value=f"> ID: **#{feedback.feedback_id}**\n> Feed: **{feed.feed_name}**\n> Label: **{label.label_name if label else 'None'}**")
    embed.add_field(name='User', value=f"> Name: **{escape_markdown(ctx.author.name)}#{ctx.author.discriminator}**\n> ID: **{ctx.author.id}**\n> Mention: {ctx.author.mention}")
    embed.add_field(name='Author', value=f"> Name: **{escape_markdown(author.name)+'#'+author.discriminator if author else '???'}**\n> ID: **{feedback.feedback_author}**\n> Mention: {author.mention if author else '**???**'}")

    await log_channel.send(embed=embed)