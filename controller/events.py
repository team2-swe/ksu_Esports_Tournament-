import discord
from discord.ui import View, Button
from discord.ext import commands
from model import dbc_model
from view.sighnUp_view import SignUpView
from model.button_state import ButtonState, first_login_users
from config import settings


logger = settings.logging.getLogger("discord")

class EventsController(commands.Cog):
    def __init__(self, bot:commands.bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member:discord.Member):
        player = self.player_model.get_by_id(member.id)

        if member.id not in first_login_users and player is None:
            first_login_users[member.id] = True

            button_state = ButtonState()
            signUp_view = SignUpView(button_state)

            if signUp_view.children:
                await member.send(f"welcome to {member.guild.name} server")
                message = await member.send(view=signUp_view)

                signUp_view.message = message

                await signUp_view.wait()

                if button_state.buttons_state is None:
                    logger.info(f"member id:{member.id} loged in the first time")

                if button_state.buttons_state is True:
                    logger.info(f"member id:{member.id} successfully sign up")

            else:
                logger.error("signup view is not working please take a look")
                server_owner = member.guild.owner

                await server_owner.send(f"Hello {server_owner} the signup view is not working please check")


async def setup(bot):
    await bot.add_cog(EventsController(bot))