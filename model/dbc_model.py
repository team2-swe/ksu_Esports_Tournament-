# import peewee
# from common.database_connection import tournament_dbc
from datetime import datetime
from config import settings
import sqlite3
import json

logger = settings.logging.getLogger("discord")

class Tournament_DB:
    def __init__(self, db_name=settings.DATABASE_NAME):
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.db_connect()

    #connection to DB
    #The default out put of sqlit3 is a list of tubles
    #Inorder to get list of dictionary data format, we use row_factory
    def db_connect(self):
        self.connection = sqlite3.connect(self.db_name)
        # self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")

    def close_db(self):
        if self.connection:
            self.connection.commit()
            self.connection.close()

class Player(Tournament_DB):
    
    def createTable(self):

        player_table_query = """
            create table if not exists player (
            user_id bigint PRIMARY KEY,
            game_name text,
            game_id text,
            tag_id text text not null,
            isAdmin integer not null default 0,
            last_modified text default (datetime('now'))
        )
        """
        self.cursor.execute(player_table_query)
        self.connection.commit()

    def register(self, interaction, gamename, tagid):
        register_query = "insert into player(user_id, game_name, tag_id) values(?, ?, ?)"

        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                self.cursor.execute(register_query, (uniq_user_id, gamename, tagid))
                self.connection.commit()
            else:
                logger.error(f"Registration ahs failed because of Non user id")
        except Exception as ex:
            logger.error(f"Registeration has failed with error {ex}")

    def fetch(self, interaction):
        query = "select * from player where user_id = ?"
        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                value = (uniq_user_id,)
                self.cursor.execute(query, value)
                return self.cursor.fetchone()
            else:
                logger.error(f"fetch ahs failed because of Non user id")
        except Exception as ex:
            logger.error(f"fetch has failed with error {ex}")
    
    def fetch_by_id(self, user_id):
        query = "select user_id, game_name from player where user_id = ?"
        try:
            value = (user_id,)
            self.cursor.execute(query, value)
            return self.cursor.fetchone()
        except Exception as ex:
            logger.error(f"fetch_by_id has failed with error {ex}")

    def update_details(self, user_id, player_rank):
        register_query = """
            update player
            set rank = ?
            where user_id = ?
        """

        try:
            self.cursor.execute(register_query, (player_rank, user_id))
            self.connection.commit()
            
        except Exception as ex:
            logger.error(f"update player details has failed with error {ex}")

    def isAcountExist(self, interaction):
        query = "select * from player where user_id = ?"
        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                value = (uniq_user_id,)
                self.cursor.execute(query, value)
                result = self.cursor.fetchone()

                return result is not None
            else:
                logger.error(f"is account exsit failed because of Non user id")
                return False
        except Exception as ex:
            logger.error(f"is account exsit  failed with error {ex}")

    def isMemberExist(self, member_id):
        query = "select * from player where user_id = ?"
        try:
            value = (member_id,)
            self.cursor.execute(query, value)
            result = self.cursor.fetchone()

            return result is not None
        except Exception as ex:
            logger.error(f"isMemberExist has failed with error {ex}")

    def get_all_player(self):
        query = "select user_id, game_name, tag_id from player"
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(f"get_all_player has failed with error {ex}")

    def remove_player(self, member_id):
        query = "delete from player where user_id = ?"
        try:
            value = (member_id,)
            self.cursor.execute(query, value)
            self.connection.commit()
        except Exception as ex:
            logger.error(f"unable to delete a user_id {member_id} from db with error {ex}")

class Game(Tournament_DB):
    
    def createTable(self):

        game_table_query = """
            CREATE TABLE IF NOT EXISTS game (
            user_id bigint not null,
            game_name text PRIMARY KEY,
            tier text,
            rank text,
            role text,
            wins integer,
            losses integer,
            toxicity integer,
            mvps integer,
            wr float generated always as (wins * 1.0 / (wins + losses)) stored,
            game_date text default (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES player (user_id) ON DELETE CASCADE
        )
        """
        self.cursor.execute(game_table_query)
        self.connection.commit()

    def update_pref(self, interaction, pref):
        register_query = "insert or replace into game(user_id, game_name, role) values(?, ?, ?)"
        pref = json.dumps(pref)
        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                pl = Player.fetch_by_id(self, uniq_user_id)
                self.cursor.execute(register_query, (uniq_user_id,pl[1], pref))
                self.connection.commit()
            else:
                logger.error(f"update_role ahs failed because of Non user id")
        except Exception as ex:
            logger.error(f"update_role has failed with error {ex}")

    def update_role(self, interaction, role):
        register_query = "insert into game(user_id, role) values(?, ?)"
        role = json.dumps(role)
        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                self.cursor.execute(register_query, (uniq_user_id, role))
                self.connection.commit()
            else:
                logger.error(f"update_role has failed because of None user id")
        except Exception as ex:
            logger.error(f"update_role has failed with error {ex}")

    def update_player_API_info(self, player_id, game_name, tier, rank, wins, losses):
        register_query = "insert or replace into Game(user_id, game_name, tier, rank, wins, losses) values(?, ?, ?, ?, ?, ?)"
        try:
            self.cursor.execute(register_query, (player_id, game_name, tier, rank, wins, losses))
            self.connection.commit()
            
        except Exception as ex:
            logger.error(f"update_player_API_info {game_name} has failed with error {ex}")

    def fetchGameDetails(self):
        query = "select user_id, game_name, tier, rank, role, wr from Game"
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(f"fetchGameDetails has failed with error {ex}")
    
class Matches(Tournament_DB):
    
    def createTable(self):

        game_table_query = """
            CREATE TABLE IF NOT EXISTS Matches (
            user_id bigint,
            game_name text,
            win text,
            loss text,
            teamUp text,
            teamId text,
            date_played date,
            FOREIGN KEY (user_id) REFERENCES player (user_id) ON DELETE CASCADE,
            FOREIGN KEY (game_name) REFERENCES player (game_name) ON DELETE CASCADE
        )
        """
        self.cursor.execute(game_table_query)
        self.connection.commit()