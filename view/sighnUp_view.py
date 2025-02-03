import discord
from model.button_state import ButtonState

class SignUpView(discord.ui.View):
    def __init__(self, buttonState, timeout = 10):
        super().__init__(timeout=timeout)
        self.button_state = buttonState

    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        #await self.message.delete()  --we can delete the messgae at all
        await self.message.edit(view=self)
        


    async def on_timeout(self) -> None:
        await self.message.channel.send("this action is timed out, please use a command to register")
        await self.disable_all_items()

    @discord.ui.button(label="signUp", style=discord.ButtonStyle.success)
    async def signUp(self, interaction: discord.Interaction, button:discord.ui.Button):
        await interaction.response.send_message("Thnaks for submission")
        self.buttonState.set_button_state(True)
        self.stop()


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def Cancel(self, interaction: discord.Interaction):
        await interaction.response.send_message("sure ignore for now")
        self.buttonState.set_button_state(True)
        self.stop()
