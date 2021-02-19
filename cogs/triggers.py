import discord
from discord.ext import commands
import asyncio

from feedback import commands as cmd
from feedback import models
from cogs._events import CustomException

class triggers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="create", aliases=['new', 'add'])
    async def create_feedback(self, ctx, feed_shortname):
        feed = models.Feed.find(ctx.guild.id, feed_shortname)
        await cmd.create_feedback(ctx, feed)

    @models.has_perms(level=2)
    @commands.command(invoke_without_subcommand=True, aliases=['trigger'])
    async def triggers(self, ctx, *args):
        if not args:
            await cmd.show_triggers(ctx)
        
        elif args[0].lower() in ['create', 'new', 'add']:
            await cmd.create_trigger(ctx)
        
        elif len(args) == 1:
            trigger = models.Trigger.find(ctx.guild.id, args[0])
            await cmd.show_trigger(ctx, trigger)

        else:
            trigger = models.Trigger.find(ctx.guild.id, args[0])
            # f!trigger <trigger> delete
            if args[1].lower() in ['delete', 'remove']:
                await cmd.delete_feed(ctx, trigger)
            # f!trigger <trigger> feed
            elif args[1].lower() in ['feed']:
                if len(args) >= 3: await cmd.set_trigger_feed(ctx, trigger, args[2])
                else: await cmd.show_trigger_feed(ctx, trigger)
            # f!trigger <trigger> feed
            elif args[1].lower() in ['emoji']:
                if len(args) >= 3: await cmd.set_trigger_emoji(ctx, trigger, args[2])
                else: await cmd.show_trigger_emoji(ctx, trigger)
            # f!trigger <trigger> feed
            elif args[1].lower() in ['message', 'msg']:
                if len(args) >= 3: await cmd.set_trigger_message(ctx, trigger, args[2])
                else: await cmd.show_trigger_message(ctx, trigger)
            
            else:
                raise CustomException('Invalid argument!', f'"{args[1]}" isn\'t a valid argument for triggers')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        
        trigger = None
        feedback = None
        try: feedback = models.Feedback(options={'message_id': payload.message_id})
        except:
            try: trigger = models.Trigger(options={'message_id': payload.message_id, 'trigger_emoji': str(payload.emoji)})
            except: pass
        
        if feedback or trigger:
            guild = self.bot.get_guild(payload.guild_id)
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            if not message: return
            ctx = await self.bot.get_context(message)
            ctx.author = payload.member

        if feedback:
            feed = feedback.feed
            emojis = feed.reactions.split(',')
                
            if str(payload.emoji) == "✍️":
                await message.remove_reaction(payload.emoji, payload.member)
                if payload.member.id == feedback.feedback_author or await models.has_perms(level=1).predicate(ctx):
                    await cmd.edit_feedback(ctx, feed, feedback)
            elif str(payload.emoji) == "🗑️":
                await message.remove_reaction(payload.emoji, payload.member)
                if payload.member.id == feedback.feedback_author or await models.has_perms(level=1).predicate(ctx):
                    feedback.delete()
                    await message.delete()
            elif feed.reactions and str(payload.emoji) not in emojis:
                for reaction in message.reactions:
                    if reaction.emoji == payload.emoji and reaction.count == 1:
                        if not await models.has_perms(level=1).predicate(ctx):
                            await message.clear_reaction(reaction.emoji)

        elif trigger:
            feed = trigger.feed
            await message.remove_reaction(payload.emoji, payload.member)
            await cmd.create_feedback(ctx, feed)

               

    
def setup(bot):
    bot.add_cog(triggers(bot))