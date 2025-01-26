import peewee
from common.database_connection import tournament_dbc
import datetime

class Player(peewee.Model):
    discord_id : int = peewee.IntegerField(unique=True, primary_key=True)
    player_username :str = peewee.CharField(max_length=50)
    
    #to connect the model with DB
    class Meta:
        database = tournament_dbc

    @staticmethod
    def fetch(interaction):
        try:
            player = Player.get(Player.discord_id == interaction.user.id)
        except peewee.DoesNotExist:
            player = Player.create(discord_id=interaction.user.id, player_username=interaction.user.name)
        return player


class Game(peewee.Model):
    discord_id : int = peewee.ForeignKeyField(Player, backref='discord_id')
    username :str = peewee.CharField()
    game_date = peewee.DateField

    #to connect the model with DB
    class Meta:
        database = tournament_dbc


    @staticmethod
    def fetch(message):
        try:
            player = Game.get(Game.discord_id == message.author.id)
        except peewee.DoesNotExist:
            player = Game.create(discord_id=message.author.id, player_username=message.author.tag, game_date=datetime.datetime.now())
        return player