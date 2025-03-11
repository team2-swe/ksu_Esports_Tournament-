import discord
from model.giveaway_model import GiveawayModel
from model.dbc_model import Player_game_info, Tournament_DB


class GiveawayView:
    @staticmethod
    async def send_confirmation_message(interaction: discord.Interaction, top, random):
        """Send the confirmation message with the details."""
        confirm_message = f"Do you want to proceed with the giveaway?\nfor the first {top} top players and\n{random} random pick"
        
        # Create submit and cancel buttons
        submit_button = discord.ui.Button(label="Submit", style=discord.ButtonStyle.green)
        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.red)

        # Attach the callback functions to the buttons
        submit_button.callback = lambda interaction: GiveawayView.submit_callback(interaction, top=top, random=random)
        cancel_button.callback = GiveawayView.cancel_callback

        # Create a view and add buttons to it
        view = discord.ui.View()
        view.add_item(submit_button)
        view.add_item(cancel_button)

        await interaction.response.send_message(confirm_message, view=view)

    @staticmethod
    async def submit_callback(interaction, top, random):
        """Handle the submission of the giveaway."""
        # prize_winners = await interaction.message.embeds[0].description.split("\n")
        winners_list, pickedList = GiveawayView.pick_winners(top, random)

        if winners_list or pickedList:           
            await interaction.response.send_message(f"winneres list \n Top {top} players {winners_list} \n Randomely picked {random} are {pickedList}")
        else:
            await interaction.response.send_message(f"")

    @staticmethod
    async def cancel_callback(interaction):
        """Handle the cancellation of the giveaway."""
        await interaction.response.send_message("The giveaway has been canceled.")

    @staticmethod
    def pick_winners(top, random):
        """Select winners from the guild members."""
        # Assuming `model` is passed or is part of a larger context
        model = GiveawayModel()  
        db = Tournament_DB()
        top_result = Player_game_info.giveaway_top(db, top=top)
        all_result = Player_game_info.for_giveaway(db, top=top)
        db.close_db()
        topPlayer, randomPicked = model.pick_winners(top_result, all_result, random)
        return topPlayer, randomPicked 