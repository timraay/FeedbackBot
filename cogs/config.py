import discord
from discord.ext import commands

from utils import add_empty_fields
from feedback import commands as cmd
from feedback import models
from cogs._events import CustomException

class config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @models.has_perms(level=2)
    @commands.command(aliases=['cf'])
    async def config(self, ctx, option: str = None, *, value: str = None):
        guild = models.Guild(ctx.guild.id)
        if not option:
            admin_role = ctx.guild.get_role(guild.admin_role)
            mod_role = ctx.guild.get_role(guild.mod_role)
            log_channel = ctx.guild.get_text_channel(guild.log_channel)
            
            embed = discord.Embed(title=f"Configuration for guild \"{ctx.guild.name}\"")
            embed.add_field(name='Command Prefix', value=f"ID: `command_prefix`\nValue: **{guild.command_prefix}**\n\n*The prefix used to invoke commands with*")
            embed.add_field(name='Admin Role', value=f"ID: `admin_role`\nValue: **{admin_role.mention if admin_role else 'None'}**\n\n*The role that can setup and customize the bot*")
            embed.add_field(name='Moderator Role', value=f"ID: `mod_role`\nValue: **{mod_role.mention if mod_role else 'None'}**\n\n*The role that can view and delete feedback*")
            embed.add_field(name='Log Channel', value=f"ID: `log_channel`\nValue: **{log_channel.mention if log_channel else 'None'}**\n\n*The channel all actions will be logged in*")
            embed = add_empty_fields(embed)
            embed.add_field(name="‏", value=f"To edit one of the values, type `{ctx.prefix}config <option> <value>`.", inline=False)

        else:
            if not value: raise CustomException('Missing required argument!', '\"value\" is a required argument that is missing')

            if option.lower() in ["prefix", "commandprefix", "command_prefix"]:
                if len(value) > 10: raise CustomException('Invalid prefix!', 'Command prefix can\'t be longer than 10 characters')

                embed = discord.Embed(color=discord.Color(7844437))
                embed.set_author(name="Command prefix updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
                embed.add_field(name="Old value", value=guild.command_prefix)
                embed.add_field(name="New value", value=value)

                guild.command_prefix = value
                guild.save()
            
            elif option.lower() in ["admin", "adminrole", "admin_role"]:
                try: new_role = await commands.RoleConverter().convert(ctx, value)
                except commands.BadArgument: raise CustomException('Invalid role!', f'Couldn\'t find a role with argument "{value}"')
                old_role = ctx.guild.get_role(guild.admin_role)

                embed = discord.Embed(color=discord.Color(7844437))
                embed.set_author(name="Admin role updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
                embed.add_field(name="Old value", value=old_role.mention if old_role else 'None')
                embed.add_field(name="New value", value=new_role.mention)

                guild.admin_role = new_role.id
                guild.save()

            elif option.lower() in ["mod", "modrole", "mod_role", "moderator", "moderatorrole", "moderator_role"]:
                try: new_role = await commands.RoleConverter().convert(ctx, value)
                except commands.BadArgument: raise CustomException('Invalid role!', f'Couldn\'t find a role with argument "{value}"')
                old_role = ctx.guild.get_role(guild.mod_role)

                embed = discord.Embed(color=discord.Color(7844437))
                embed.set_author(name="Moderator role updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
                embed.add_field(name="Old value", value=old_role.mention if old_role else 'None')
                embed.add_field(name="New value", value=new_role.mention)

                guild.mod_role = new_role.id
                guild.save()
            
            elif option.lower() in ["log", "logchannel", "log_channel", "logs", "logschannel", "logs_channel"]:
                try: new_channel = await commands.TextChannelConverter().convert(ctx, value)
                except commands.BadArgument: raise CustomException('Invalid channel!', f'Couldn\'t find a channel with argument "{value}"')
                old_channel = ctx.guild.get_text_channel(guild.log_channel)

                embed = discord.Embed(color=discord.Color(7844437))
                embed.set_author(name="Log channel updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
                embed.add_field(name="Old value", value=old_channel.mention if old_role else 'None')
                embed.add_field(name="New value", value=new_channel.mention)

                guild.log_channel = new_channel.id
                guild.save()

            else:
                raise CustomException('Invalid option!', f'"{option}" isn\'t a configuration option')

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(config(bot))