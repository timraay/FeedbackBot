import discord
from discord.ext import commands
import io
import json
import re

from feedback import commands as cmd, models
from cogs._events import CustomException

class feedback(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @models.has_perms(level=1)
    @commands.command()
    async def export(self, ctx, format: str = "csv"):
        if format.lower() == "csv":
            csv = "Feed,Label,ID,Author,Message,Media"
            all_feedback = models.Guild(ctx.guild.id).feedback
            for feedback in all_feedback:
                feed = models.Feed('feed_id', feedback.feed_id)
                feed_name = feed.feed_name.replace(",", "\\,")
                label_name = models.Label('label_id', feedback.label_id).label_name.replace(",", "\\,") if feedback.label_id else ''
                user = self.bot.get_user(feedback.feedback_author)
                author = str(user).replace(",", "\\,") if user else str(feedback.feedback_author)
                desc = feedback.feedback_desc.replace(',', '\\,').replace('\n', '\\n')
                csv += f"\n{feed_name},{label_name},{feedback.feedback_id},{author},{desc},{feedback.feedback_desc_url}"
            iofile = io.StringIO()
            iofile.write(csv)
            iofile.seek(0)
            f = discord.File(iofile, filename=f"{ctx.guild.name} feedback.csv")
        
        elif format.lower() == "json":
            data = dict()
            guild = models.Guild(ctx.guild.id)
            data['guild_id'] = ctx.guild.id
            data['guild_name'] = ctx.guild.name
            data['feeds'] = list()
            for feed in guild.feeds:
                feed_data = dict()
                feed_data['feed_name'] = feed.feed_name
                feed_data['feed_shortname'] = feed.feed_shortname
                feed_data['feed_color'] = "#"+feed.feed_color
                feed_data['feed_desc'] = feed.feed_desc
                feed_data['feed_desc_url'] = feed.feed_desc_url
                feed_data['feed_channel_id'] = feed.feed_channel_id
                feed_data['labels'] = list()
                for label in feed.labels:
                    label_data = dict()
                    label_data['label_id'] = label.label_id
                    label_data['label_name'] = label.label_name
                    label_data['label_shortname'] = label.label_shortname
                    label_data['label_color'] = "#"+label.label_color
                    label_data['label_desc'] = label.label_desc
                    label_data['label_desc_url'] = label.label_desc_url
                    label_data['label_emoji'] = label.label_emoji
                    feed_data['labels'].append(label_data)
                feed_data['feedback'] = list()
                for feedback in feed.feedback:
                    feedback_data = dict()
                    feedback_data['feedback_id'] = feedback.feedback_id
                    feedback_data['label_id'] = feedback.label_id
                    feedback_data['feedback_author'] = feedback.feedback_author
                    feedback_data['feedback_desc'] = feedback.feedback_desc
                    feedback_data['feedback_desc_url'] = feedback.feedback_desc_url
                    feed_data['feedback'].append(feedback_data)
                feed_data['triggers'] = list()
                for trigger in feed.triggers:
                    trigger_data = dict()
                    trigger_data['trigger_emoji'] = trigger.trigger_emoji
                    trigger_data['trigger_channel_id'] = trigger.trigger_channel_id
                    trigger_data['trigger_message_id'] = trigger.trigger_message_id
                    feed_data['triggers'].append(trigger_data)
                data['feeds'].append(feed_data)
            iofile = io.StringIO()
            iofile.write(json.dumps(data, indent=2))
            iofile.seek(0)
            f = discord.File(iofile, f"{ctx.guild.name} feedback.json")

        else:
            raise CustomException('Invalid export type!', f'Expected either "csv" or "json", not "{format.lower()}"')
        embed = discord.Embed(color=discord.Color(7844437))
        embed.set_author(name=f"Successfully exported!", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
        await ctx.send(embed=embed, file=f)

    @models.has_perms(level=1)
    @commands.group(invoke_without_command=True, aliases=['fb'])
    async def feedback(self, ctx, feed_shortname, feedback_id: int, action: str = None):
        feed = models.Feed.find(ctx.guild.id, feed_shortname)
        feedback = models.Feedback(feed.feed_id, 'feedback_id', feedback_id)
        if not action:
            await cmd.show_feedback(ctx, feed, feedback)
        elif action.lower() in ["delete", "remove"]:
            await cmd.delete_feedback(ctx, feed, feedback)
    
    @models.has_perms(level=1)
    @feedback.command()
    async def user(self, ctx, user: discord.User):
        feedbacks = models.get_feedback_by_user_id(user.id)
        embed = discord.Embed()
        if feedbacks:
            embed.title = f"{user.name} has {str(len(feedbacks))} messages."
            embed.description = ""
            for feedback in feedbacks:
                try: message = await commands.MessageConverter().convert(ctx, f'{feedback.channel_id}-{feedback.message_id}')
                except commands.BadArgument: message = None
                if message: jump = f"[Jump to message]({message.jump_url})"
                else: jump = "No message ⚠️"
                label = feedback.label
                embed.description += f"**#{feedback.feedback_id}** | {feedback.feed.feed_name}{f' ({label.label_name})' if label else ''} - {jump}\n"
        else:
            raise CustomException(f"{user.name} doesn't have any feedback yet!", "")

        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        try: feedback = models.Feedback.find(payload.channel_id, payload.message_id)
        except models.NotFound: pass
        else: feedback.delete()


def setup(bot):
    bot.add_cog(feedback(bot))