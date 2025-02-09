import peewee
from common.database_connection import tournament_dbc
from datetime import datetime
from config import settings

class Player(peewee.Model):
    user_id : str = peewee.CharField(unique=True, primary_key=True)
    game_name : str = peewee.CharField(null=True)
    game_id : str = peewee.CharField(null=True)
    tag_id : str = peewee.CharField(null=True)
    rank : str = peewee.CharField(null=True)
    isAdmin : bool = peewee.BooleanField(default=False)
    last_modified = peewee.DateTimeField(default=datetime.now)
    
    
    #to connect the model with DB
    class Meta:
        database = tournament_dbc

    @staticmethod
    def register(interaction, gamename, tagid):
        try:
            uniq_user_id = interaction.user.id
            print(f"game name: {gamename} and tage id is {tagid} {interaction.user.id}")

            if not uniq_user_id:
                print(f"user id is not set")
            else:    
                player_created, created = Player.get_or_create(user_id=uniq_user_id)
                player_created.game_name = gamename
                player_created.tag_id = tagid

                player_created.save()
            # # player = Player.create(discord_id=interaction.user.id.id, player_username=interaction.user.id.name, game_name=gamename, tag_id=tagid)
            # return player
        except Exception as ex:
            print(f"There is an error while item added into DB {ex}")
    
    
    @staticmethod
    def fetch(interaction):
        try:
            player = Player.get(Player.discord_id == interaction.user.id)
        except peewee.DoesNotExist:
            player = Player.create(user_id=interaction.user.id)
        return player
    
    @staticmethod
    def isAcountExist(interaction):
        acountExist : bool = False
        try:
            player = Player.get(Player.user_id == interaction.user.id)
            if player and player.tag_id:
                acountExist = True
        except peewee.DoesNotExist:
            acountExist = False
        return acountExist
    #Dynamic method used for CRUD based on the two methods get_or_create and save() 
    @staticmethod
    def update_player_details(player_guidId, player_rank):
        Player, created = Player.get_or_create(user_id=player_guidId)

        Player.rank = player_rank

        Player.save()



class Game(peewee.Model):
    user_id : int = peewee.ForeignKeyField(Player, backref='user_id')
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
            player = Game.get(Game.user_id == message.author.id)
        except peewee.DoesNotExist:
            player = Game.create(user_id=message.author.id, player_username=message.author.tag, game_date=datetime.datetime.now())
        return player
    
    @staticmethod
    def update_role_pref(interaction, pref, role):
        try:
            game = Game.create(user_id=interaction.user.id, preference=pref, role=role, game_date=datetime.datetime.now())
            return game
        except Exception as ex:
            print(f"There is an error while item added into DB {ex}")