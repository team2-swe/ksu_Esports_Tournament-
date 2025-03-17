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

    def close_db(self):
        if self.connection:
            self.connection.commit()
            self.connection.close()
    
    def calculate_manual_tier(self, tier, rank):
        """Calculate a manual tier value (0-10) based on tier and rank"""
        # Base tier values mapped to 0-10 scale 
        tier_values = {
            "iron": 0,
            "bronze": 1,
            "silver": 3,
            "gold": 5,
            "platinum": 6.5,
            "emerald": 7.5,
            "diamond": 8.5,
            "master": 9.0,
            "grandmaster": 9.5,
            "challenger": 10.0,
            "default": 0
        }
        
        # Rank adjustments (divisions within tier)
        rank_adjustments = {
            "IV": 0.0,
            "III": 0.25,
            "II": 0.5,
            "I": 0.75
        }
        
        # Get base tier value
        tier_value = tier_values.get(tier.lower(), tier_values["default"])
        
        # Add rank adjustment
        if rank in rank_adjustments:
            # For tiers below master, add the rank adjustment
            if tier.lower() not in ["master", "grandmaster", "challenger"]:
                tier_value += rank_adjustments[rank]
        
        return round(tier_value, 2)

class Player(Tournament_DB):
    
    def createTable(self):

        player_table_query = """
            create table if not exists player (
            user_id bigint PRIMARY KEY,
            game_name text not null,
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
        query = "select * from player where user_id = ?"
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
            game_name text not null,
            tier text,
            rank text,
            role text,
            wins integer,
            losses integer,
            manual_tier float DEFAULT NULL,
            wr float generated always as (wins * 1.0 / (wins + losses)) stored,
            game_date text default (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES player (user_id) ON DELETE CASCADE,
            FOREIGN KEY (game_name) REFERENCES player (game_name) ON DELETE CASCADE
        )
        """
        self.cursor.execute(game_table_query)
        self.connection.commit()

    def update_pref(self, interaction, pref):
        register_query = "insert into game(user_id, game_name, role) values(?, ?, ?)"
        pref = json.dumps(pref)
        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                # Get player's game_name from the player table
                self.cursor.execute("SELECT game_name FROM player WHERE user_id = ?", (uniq_user_id,))
                player_data = self.cursor.fetchone()
                
                if not player_data:
                    # If player not found, use a default game name
                    game_name = "League of Legends"
                else:
                    game_name = player_data[0]
                
                self.cursor.execute(register_query, (uniq_user_id, game_name, pref))
                self.connection.commit()
            else:
                logger.error(f"update_pref has failed because of Non user id")
        except Exception as ex:
            logger.error(f"update_pref has failed with error {ex}")

    def update_role(self, interaction, role):
        register_query = "insert into game(user_id, game_name, role) values(?, ?, ?)"
        role = json.dumps(role)
        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                # Get player's game_name from the player table
                self.cursor.execute("SELECT game_name FROM player WHERE user_id = ?", (uniq_user_id,))
                player_data = self.cursor.fetchone()
                
                if not player_data:
                    # If player not found, use a default game name
                    game_name = "League of Legends"
                else:
                    game_name = player_data[0]
                
                self.cursor.execute(register_query, (uniq_user_id, game_name, role))
                self.connection.commit()
            else:
                logger.error(f"update_role has failed because of Non user id")
        except Exception as ex:
            logger.error(f"update_role has failed with error {ex}")

    def update_player_API_info(self, player_id, tier, rank, wins, losses):
        # Calculate manual tier value automatically based on tier and rank
        manual_tier = self.calculate_manual_tier(tier, rank)
        
        register_query = "insert into Game(user_id, tier, rank, wins, losses, manual_tier) values(?, ?, ?, ?, ?, ?)"

        try:
            self.cursor.execute(register_query, (player_id, tier, rank, wins, losses, manual_tier))
            self.connection.commit()
            
        except Exception as ex:
            logger.error(f"update_player_API_info has failed with error {ex}")
    
    # This function is now defined in the Tournament_DB class
    
    def get_manual_tier(self, player_id):
        """Get a player's manual tier value"""
        query = """
            SELECT manual_tier, tier, rank
            FROM game
            WHERE user_id = ?
            ORDER BY game_date DESC
            LIMIT 1
        """
        
        try:
            self.cursor.execute(query, (player_id,))
            result = self.cursor.fetchone()
            
            if result:
                manual_tier, tier, rank = result
                
                # If manual_tier is None, calculate it based on tier and rank
                if manual_tier is None and tier:
                    calculated_value = self.calculate_manual_tier(tier, rank)
                    self.update_manual_tier(player_id, calculated_value)
                    return calculated_value
                    
                return manual_tier
                
            return None
        except Exception as ex:
            logger.error(f"get_manual_tier failed with error {ex}")
            return None
    
    def update_manual_tier(self, player_id, manual_tier):
        """Update a player's manual tier value directly"""
        # Check if player has a game record
        query = "SELECT COUNT(*) FROM game WHERE user_id = ?"
        
        try:
            self.cursor.execute(query, (player_id,))
            count = self.cursor.fetchone()[0]
            
            if count > 0:
                # Update existing record with the manual tier
                update_query = """
                    UPDATE game 
                    SET manual_tier = ?
                    WHERE user_id = ? AND game_date = (
                        SELECT MAX(game_date) FROM game WHERE user_id = ?
                    )
                """
                self.cursor.execute(update_query, (manual_tier, player_id, player_id))
                self.connection.commit()
                return True
            else:
                # Cannot set manual tier if no game record exists
                return False
                
        except Exception as ex:
            logger.error(f"update_manual_tier failed with error {ex}")
            return False
            
    def update_player_tier(self, player_id, tier, rank):
        """Update a player's tier and rank in the Game table"""
        # First check if the player already has a game entry
        query = "SELECT COUNT(*) FROM game WHERE user_id = ?"
        
        try:
            self.cursor.execute(query, (player_id,))
            count = self.cursor.fetchone()[0]
            
            if count > 0:
                # Update existing record with the most recent game_date
                update_query = """
                    UPDATE game 
                    SET tier = ?, rank = ?
                    WHERE user_id = ? AND game_date = (
                        SELECT MAX(game_date) FROM game WHERE user_id = ?
                    )
                """
                self.cursor.execute(update_query, (tier, rank, player_id, player_id))
            else:
                # Create a new entry
                insert_query = "INSERT INTO game(user_id, tier, rank) VALUES(?, ?, ?)"
                self.cursor.execute(insert_query, (player_id, tier, rank))
                
            self.connection.commit()
            return True
        except Exception as ex:
            logger.error(f"update_player_tier has failed with error {ex}")
            return False

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