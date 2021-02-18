import discord
from discord.ext import commands
import random
from random import randint
import os
import ast


HELP_DEFAULT = """
:wave: Hello, I am **FeedbackBot**! Like the name suggests, I'm a utility to help you gather feedback in an effective and clean manner. Before I explain to you what each command does, it is recommended you read this page first.

I operate on a **guild**-wide basis. In case you didn't know, a guild is the official term for a Discord server. As an admin, you can create **feeds** for this guild. A feed is nothing more than a channel that members of your guild can submit feedback to.

For each feed, you can (but don't have to) create **labels**. Members can assign a pre-defined label to their feedback to further categorize it.

And finally we have **triggers**. Triggers are reactions under a message which members may react with to start creating feedback for the feed it is bound to. This too is completely optional, but it is a lot cleaner than running a command.

Now that you understand the basic terms, we can move on. Using the command `f!help [topic]` you can read more about specifics and how to set them up. Available topics are feeds, labels, triggers, feedback, permissions.
"""
HELP_FEEDS = """
A feed consists of 5 elements: The name, shortname, color, description, and channel.

The name is displayed above all feedback. The shortname is used to reference your feed in commands. It should be a simplified version of your feed's name. The color of the feed translates to the colored bar on the left side of this message. The feed's channel is where all feedback will be sent to. Additionally, there's an option to make feedback in this feed anonymous.

Feeds can be accessed using one main command, `f!feed`! Alternatively, you can also use its plural `f!feeds`.

**Creating a feed**

Creating a feed is simple. You run the command `f!feed create`. This will initiate the creation process. Here it will ask you step by step for all above mentioned elements. Follow the instructions it gives you. Once you finish, you can now view your feed using the `f!feed <feed>` command. Creating a feed requires admin permissions.

**Customizing a feed**

The below commands can be used to show or modify properties of an already existing feed.```
f!feed <feed> name [new_value..]
f!feed <feed> shortname [new_value..]
f!feed <feed> desc [new_value..]
f!feed <feed> color [new_value]
f!feed <feed> channel [new_value..]
f!feed <feed> anonymous [new_value]
```
To delete a feed, use `f!feed <feed> delete`.
"""
HELP_LABELS = """
Labels are a way of further categorizing feedback. Just like feeds, labels have a name, shortname, color, description, but also an emoji. The label's color will overwrite the feed's color, whereas the label's name and description are displayed alongside the feed's. The emoji is used in the feedback creation process to select a label.

Since labels are an extension of feeds, you can access them using the command `f!feed <feed> labels`. Using `label` instead of `labels` will also work.

**Creating a label**

Creating a label is similar to creating a feed. Run the command `f!feed <feed> label create` and follow the instructions. Once you finish, you can now view your label using the `f!feed <feed> label <label>` command. Creating a label requires admin permissions.

**Customizing a label**

The below commands can be used to show or modify properties of an existing label.```
f!feed <feed> label <label> name [new_value..]
f!feed <feed> label <label> shortname [new_value..]
f!feed <feed> label <label> desc [new_value..]
f!feed <feed> label <label> color [new_value]
f!feed <feed> label <label> emoji [new_value]
```
To delete a label, use `f!feed <feed> label <label> delete`.
"""
HELP_TRIGGERS = """
Triggers are a more fancy way of letting users create feedback. Instead of having to run a command, users can react to a message. A trigger consists of 3 elements: An emoji, a message users can react to with the given emoji, and a feed to create feedback for once triggered.

While each trigger is specific to a single feed, they are treated as standalone objects, unlike labels. For that reason they have their own command, `f!triggers` (or `f!trigger`, additionally). Creating a trigger requires admin permissions.

**Creating a trigger**

Even for triggers, there is a creation process. Run the command `f!trigger create` and follow the instructions. Once you finish, you can view your trigger using the `f!trigger <trigger>` command. Since triggers have no shortname, you have to select them by index.

**Customizing a trigger**

The below commands can be used to show or modify properties of an existing trigger.```
f!triggers <trigger> feed [value]
f!triggers <trigger> emoji [value]
f!triggers <trigger> message [value]
```
To delete a trigger, use `f!trigger <trigger> delete`.
"""
HELP_FEEDBACK = """
What feedback is and how to create it is all what your guild members will have to know, and it is your job to tell them. Using feed and label descriptions is a great way of giving the user some guidelines as to what to write, too.

**Creating feedback**

Feedback can be created in two ways. Users can run the `f!new <feed>` command, or trigger a trigger. When triggered, a private channel is created in the same channel category the feed is in. If there are labels available, it will first prompt you to choose one. Once that's done, you can write your actual feedback in a single message, additionally including an attachment. Finally, it will show you what your feedback will look like and ask you to confirm before sending it. If you decline, you can type your message again. When the feedback is done the channel will be removed again.

**Viewing feedback**

Feedback is sent to the feed's channel. Anyone with access to that channel can thus see the feedback message. Moderators however can also see a more detailed look of the feedback elsewhere using the `f!feedback <feed> <feedback>`, "feed" being the shortname or index of the feed and "feedback" being the ID each feedback gets (the number after the hashtag). Currently it is not possible to edit feedback. Alternatively, moderators can list all feedback sent by a specific user using the command `f!fb user <user>`.

**Deleting feedback**

Just like creating it, feedback can be deleted in two ways. You can use the command, `f!fb <feed> <feedback> delete`, or simply delete the feedback message. When feedback is being created, both the creator and moderators can cancel it by typing "cancel" at the right time.
"""
HELP_PERMISSIONS = """
By default, the only thing members can do is create feedback. Though, there's two different types of permissions you can assign to a role, to then grant to specific users.

The first permission level is moderator. This will give users access to view feedback, view feedback creation channels, and delete them. They can also export feedback using the `f!export [(csv|json)]` command.

The second permission level is administrator. This includes all the permissions a moderator has, as well as the ability to create, modify and delete feeds, labels and triggers. Admins can also change the roles these permissions are assigned to, as well as the bot's prefix, using `f!config`.

Note that if a member of your server has Discord's administrator permission, the bot will also give the user admin perms, even if the user doesn't have the so-called admin role.

**Setting up a role with permissions**

Permissions are part of the guild's config, see `f!config`. You can assign a role to have mod or admin permissions with the `f!cf (mod|admin) <role>` command. Changes are applied immediately.
"""

def insert_returns(body):
    # insert return stmt if the l expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


class _util(commands.Cog):
    """Utility commands to get help, stats, links and more"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['guide', 'guides'])
    async def help(self, ctx, category: str = None):
        embed = discord.Embed()
        if not category: embed.description = HELP_DEFAULT
        elif category.lower() in ["feed", "feeds"]: embed.description = HELP_FEEDS
        elif category.lower() in ["label", "labels"]: embed.description = HELP_LABELS
        elif category.lower() in ["feedback"]: embed.description = HELP_FEEDBACK
        elif category.lower() in ["trigger", "triggers"]: embed.description = HELP_TRIGGERS
        elif category.lower() in ["perm", "perms", "permission", "permissions", "admin", "administration", "mod", "moderation"]: embed.description = HELP_PERMISSIONS
        else: embed.description = HELP_DEFAULT
        await ctx.send(embed=embed)

        
    @commands.command()
    async def invite(self, ctx):
        oauth = discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(permissions=8))
        embed = discord.Embed(description=f"[☺️ Click here for an invite link!]({oauth})")
        await ctx.send(embed=embed)

    @commands.command(description="View my current latency", usage="r!ping")
    async def ping(self, ctx):
        latency = self.bot.latency * 1000
        color = discord.Color.dark_green()
        if latency > 150: color = discord.Color.green()
        if latency > 200: color = discord.Color.gold()
        if latency > 300: color = discord.Color.orange()
        if latency > 500: color = discord.Color.red()
        if latency > 1000: color = discord.Color(1)
        embed = discord.Embed(description=f'🏓 Pong! {round(latency, 1)}ms', color=color)
        await ctx.send(embed=embed)


    @commands.command(description="Evaluate a python variable or expression", usage="r!eval <cmd>", hidden=True)
    @commands.is_owner()
    async def eval(self, ctx, *, cmd):
        """Evaluates input.
        Input is interpreted as newline seperated statements.
        If the last statement is an expression, that is the return value.
        Usable globals:
        - `bot`: the bot instance
        - `discord`: the discord module
        - `commands`: the discord.ext.commands module
        - `ctx`: the invokation context
        - `__import__`: the builtin `__import__` function
        Such that `>eval 1 + 1` gives `2` as the result.
        The following invokation will cause the bot to send the text '9'
        to the channel of invokation and return '3' as the result of evaluating
        >eval ```
        a = 1 + 2
        b = a * 2
        await ctx.send(a + b)
        a
        ```
        """
        fn_name = "_eval_expr"

        cmd = cmd.strip("` ")
        if cmd.startswith("py"): cmd = cmd.replace("py", "", 1)

        # add a layer of indentation
        cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

        # wrap in async def body
        body = f"async def {fn_name}():\n{cmd}"

        parsed = ast.parse(body)
        body = parsed.body[0].body

        insert_returns(body)

        env = {
            'self': self,
            'discord': discord,
            'commands': commands,
            'ctx': ctx,
            '__import__': __import__
        }
        exec(compile(parsed, filename="<ast>", mode="exec"), env)

        result = (await eval(f"{fn_name}()", env))
        try:
            await ctx.send(result)
        except discord.HTTPException:
            pass

    '''
    @commands.command(description="Send a DM to all instance owners", usage="r!dm_all_owners <message>", hidden=True)
    @commands.is_owner()
    async def dm_all_owners(self, ctx, *, text: str):

        msg = await ctx.send(text + "\n\nAre you sure you want to send this message?")
        await msg.add_reaction("<:yes:809149148356018256>")

        def check_reaction(reaction, user):
            return str(reaction.emoji) == "<:yes:809149148356018256>" and user == ctx.author and reaction.message == msg
        try: reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check_reaction)
        except: await msg.clear_reactions()
        else:
            await msg.delete()

            import sqlite3
            db = sqlite3.connect('instances.db')
            cur = db.cursor()
            cur.execute('SELECT DISTINCT owner_id FROM instances')
            owner_ids = [owner_id[0] for owner_id in cur.fetchall()]
            for owner_id in owner_ids:
                try:
                    user = self.bot.get_user(owner_id)
                    await user.send(text)
                except Exception as e:
                    print(e)
                    pass
            await ctx.send("DMs sent")
    '''


def setup(bot):
    bot.add_cog(_util(bot))