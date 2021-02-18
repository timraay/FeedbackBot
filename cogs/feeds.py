import discord
from discord.ext import commands

from feedback import commands as cmd
from feedback import models
from cogs._events import CustomException

class feeds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @models.has_perms(level=2)
    @commands.command(aliases=['feed'])
    async def feeds(self, ctx, *, params=''):
        args = params.split(' ') if params else []

        """
                len(1)   len(2)   len(3)   len(4)   len(5)
                args[0]  args[1]  args[2]  args[3]  args[4]
        f!feeds <feed>   label    <label>  name     <value>
        """

        # f!feed
        if not args:
            await cmd.show_feeds(ctx)

        # f!feed create
        elif args[0].lower() in ['create', 'new', 'add']:
            await cmd.create_feed(ctx)

        # f!feed <feed>
        elif len(args) == 1:
            feed = models.Feed.find(ctx.guild.id, args[0])
            await cmd.show_feed(ctx, feed)
        
        else:
            feed = models.Feed.find(ctx.guild.id, args[0])
            # f!feed <feed> delete
            if args[1].lower() in ['delete', 'remove']:
                await cmd.delete_feed(ctx, feed)
            # f!feed <feed> name
            elif args[1].lower() in ['name']:
                if len(args) >= 3: await cmd.set_feed_name(ctx, feed, " ".join(args[2:]))
                else: await cmd.show_feed_name(ctx, feed)
            # f!feed <feed> shortname
            elif args[1].lower() in ['shortname', 'short_name']:
                if len(args) >= 3: await cmd.set_feed_shortname(ctx, feed, " ".join(args[2:]))
                else: await cmd.show_feed_shortname(ctx, feed)
            # f!feed <feed> desc
            elif args[1].lower() in ['desc', 'description']:
                if len(args) >= 3: await cmd.set_feed_desc(ctx, feed, " ".join(args[2:]))
                else: await cmd.show_feed_desc(ctx, feed)
            # f!feed <feed> color
            elif args[1].lower() in ['color']:
                if len(args) >= 3: await cmd.set_feed_color(ctx, feed, args[2])
                else: await cmd.show_feed_color(ctx, feed)
            # f!feed <feed> channel
            elif args[1].lower() in ['channel']:
                if len(args) >= 3: await cmd.set_feed_channel(ctx, feed, " ".join(args[2:]))
                else: await cmd.show_feed_channel(ctx, feed)
            # f!feed <feed> anonymous
            elif args[1].lower() in ['anonymous', 'anon']:
                if len(args) >= 3: await cmd.set_feed_anonymous(ctx, feed, args[2])
                else: await cmd.show_feed_anonymous(ctx, feed)
            # f!feed <feed> reactions
            elif args[1].lower() in ['reactions', 'reaction']:
                if len(args) >= 3: await cmd.set_feed_reactions(ctx, feed, " ".join(args[2:]))
                else: await cmd.show_feed_reactions(ctx, feed)

            elif args[1].lower() in ['labels', 'label']:
                # f!feed <feed> label
                if len(args) == 2:
                    await cmd.show_labels(ctx, feed)

                # f!feed <feed> label create
                elif args[2] in ['create', 'new', 'add']:
                    await cmd.create_label(ctx, feed)

                # f!feed <feed> label <label> 
                elif len(args) == 3:
                    label = models.Label.find(feed, args[2])
                    await cmd.show_label(ctx, feed, label)

                else: 
                    label = models.Label.find(feed, args[2])
                    # f!feed <feed> label <label> delete
                    if args[3].lower() in ['delete', 'remove']:
                        await cmd.delete_label(ctx, feed, label)
                    # f!feed <feed> label <label> name
                    elif args[3].lower() in ['name']:
                        if len(args) >= 5: await cmd.set_label_name(ctx, feed, label, " ".join(args[4:]))
                        else: await cmd.show_label_name(ctx, feed, label)
                    # f!feed <feed> label <label> shortname
                    elif args[3].lower() in ['shortname', 'short_name']:
                        if len(args) >= 5: await cmd.set_label_shortname(ctx, feed, label, " ".join(args[4:]))
                        else: await cmd.show_label_shortname(ctx, feed, label)
                    # f!feed <feed> label <label> desc
                    elif args[3].lower() in ['desc', 'description']:
                        if len(args) >= 5: await cmd.set_label_desc(ctx, feed, label, " ".join(args[4:]))
                        else: await cmd.show_label_desc(ctx, feed, label)
                    # f!feed <feed> label <label> color
                    elif args[3].lower() in ['color']:
                        if len(args) >= 5: await cmd.set_label_color(ctx, feed, label, args[4])
                        else: await cmd.show_label_color(ctx, feed, label)
                    # f!feed <feed> label <label> emoji
                    elif args[3].lower() in ['emoji']:
                        if len(args) >= 5: await cmd.set_label_emoji(ctx, feed, label, args[4])
                        else: await cmd.show_label_emoji(ctx, feed, label)

                    else:
                        raise CustomException('Invalid argument!', f'"{args[3]}" isn\'t a valid argument for labels')

            else:
                raise CustomException('Invalid argument!', f'"{args[1]}" isn\'t a valid argument for feeds')


def setup(bot):
    bot.add_cog(feeds(bot))