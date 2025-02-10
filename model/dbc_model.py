# import peewee
# from common.database_connection import tournament_dbc
from datetime import datetime
from config import settings
import sqlite3

logger = settings.logging.getLogger("discord")

class Tournament_DB:
    def __init__(self, db_name=settings.DATABASE_NAME):
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.db_connect()

    #connection to DB
    def db_connect(self):
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()

    def close_db(self):
        if self.connection:
            self.connection.commit()
            self.connection.close()

class Player(Tournament_DB):
    
    def createTable(self):

        player_table_query = """
            create table if not exists player (
            user_id bigint PRIMARY KEY,
            game_name text not null,
            game_id text,
            tag_id text text not null,
            rank text,
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
        query = "select * from player where user_id = ?"
        try:
            value = (user_id,)
            self.cursor.execute(query, value)
            return self.cursor.fetchone()
        except Exception as ex:
            logger.error(f"fetch_by_id has failed with error {ex}")

    def update_player_details(self, interaction, player_rank):
        register_query = "insert into player(user_id, rank) values(?, ?)"

        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                self.cursor.execute(register_query, (uniq_user_id, player_rank))
                self.connection.commit()
            else:
                logger.error(f"update player details ahs failed because of Non user id")
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

    def get_all_player(self, game_name):
        query = "select * from player where game_name = ?"
        try:
            value = (game_name,)
            self.cursor.execute(query, value)
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
            game_name text not null,
            tag_id text text not null,
            preference text,
            role text,
            rank text,
            tier text,
            game_date text default (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES player (user_id) ON DELETE CASCADE,
            FOREIGN KEY (game_name) REFERENCES player (game_name) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES player (tag_id) ON DELETE CASCADE,
            FOREIGN KEY (rank) REFERENCES player (rank) ON DELETE CASCADE
        )
        """
        self.cursor.execute(game_table_query)
        self.connection.commit()

    def update_role_pref(self, interaction, pref, role):
        register_query = "insert into game(user_id, preference, role) values(?, ?, ?)"

        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                self.cursor.execute(register_query, (uniq_user_id, pref, role))
                self.connection.commit()
            else:
                logger.error(f"update_role_pref ahs failed because of Non user id")
        except Exception as ex:
            logger.error(f"update_role_pref has failed with error {ex}")
