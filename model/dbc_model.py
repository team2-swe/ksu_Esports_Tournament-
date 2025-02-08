import peewee
from common.database_connection import tournament_dbc
import datetime
from config import settings

class Player(peewee.Model):
    discord_id : int = peewee.IntegerField(unique=True, primary_key=True)
    player_username :str = peewee.CharField(max_length=50)
    game_name : str = peewee.CharField(max_length=50, null=True)
    game_id : str = peewee.CharField(null=True)
    # tag_id : int = peewee.IntegerField(unique=True)
    tag_id : str = peewee.CharField(null=True)
    rank : str = peewee.CharField(null=True)
    isAdmin : bool = peewee.BooleanField(default=False)
    
    
    #to connect the model with DB
    class Meta:
        database = tournament_dbc

    @staticmethod
    def register(interaction, gamename, tagid):
        try:
            print(f"game name: {gamename} and tage id is {tagid}")
            player = Player.create(discord_id=interaction.user.id, player_username=interaction.user.name, game_name=gamename, tag_id=tagid)
            return player
        except Exception as ex:
            print(f"There is an error while item added into DB {ex}")
    
    
    @staticmethod
    def fetch(interaction):
        try:
            player = Player.get(Player.discord_id == interaction.user.id)
        except peewee.DoesNotExist:
            player = Player.create(discord_id=interaction.user.id, player_username=interaction.user.name)
        return player
    
    @staticmethod
    def isAcountExist(interaction):
        acountExist : bool = False
        try:
            player = Player.get(Player.discord_id == interaction.user.id)
            if player and player.tag_id:
                acountExist = True
        except peewee.DoesNotExist:
            acountExist = False
        return acountExist


class Game(peewee.Model):
    discord_id : int = peewee.ForeignKeyField(Player, backref='discord_id')
    game_name :str = peewee.ForeignKeyField(Player, backref='game_name')
    tag_id :str = peewee.ForeignKeyField(Player, backref='tag_id')
    preference : str = peewee.CharField(null=True)
    role : str = peewee.CharField(null=True)
    rank : str = peewee.CharField(null=True)
    tier : float = peewee.CharField(null=True)
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
    
    @staticmethod
    def update_role_pref(interaction, pref, role):
        try:
            game = Game.create(discord_id=interaction.user.id, preference=pref, role=role, game_date=datetime.datetime.now())
            return game
        except Exception as ex:
            print(f"There is an error while item added into DB {ex}")