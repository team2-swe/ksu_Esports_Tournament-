
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
            player_id bigint PRIMARY KEY,
            user_name text,
            game_name text,
            tag_id text not null,
            isAdmin integer not null default 0,
            last_modified text default (datetime('now'))
        )
        """
        self.cursor.execute(player_table_query)
        self.connection.commit()

    def register(self, interaction, gamename, tagid):
        register_query = "insert into player(player_id, user_name, game_name, tag_id) values(?, ?, ?, ?)"

        try:
            uniq_player_id = interaction.user.id
            user_name = interaction.user.name
            if uniq_player_id:
                self.cursor.execute(register_query, (uniq_player_id, user_name, gamename, tagid))
                self.connection.commit()
            else:
                logger.error(f"Registration failed because of Non user id")
        except Exception as ex:
            logger.error(f"Registeration process failed with error {ex}")

    def fetch(self, interaction):
        query = "select * from player where player_id = ?"
        try:
            uniq_player_id = interaction.user.id
            if uniq_player_id:
                value = (uniq_player_id,)
                self.cursor.execute(query, value)
                return self.cursor.fetchone()
            else:
                logger.error(f"fetch ahs failed because of Non user id")
        except Exception as ex:
            logger.error(f"fetch has failed with error {ex}")
    
    def fetch_by_id(self, player_id):
        query = "select player_id, game_name from player where player_id = ?"
        try:
            value = (player_id,)
            self.cursor.execute(query, value)
            return self.cursor.fetchone()
        except Exception as ex:
            logger.error(f"fetch_by_id has failed with error {ex}")

    def update_details(self, player_id, player_rank):
        register_query = """
            update player
            set rank = ?
            where player_id = ?
        """

        try:
            self.cursor.execute(register_query, (player_rank, player_id))
            self.connection.commit()
            
        except Exception as ex:
            logger.error(f"update player details has failed with error {ex}")

    def isAcountExist(self, interaction):
        query = "select * from player where player_id = ?"
        try:
            uniq_player_id = interaction.user.id
            if uniq_player_id:
                value = (uniq_player_id,)
                self.cursor.execute(query, value)
                result = self.cursor.fetchone()

                return result is not None
            else:
                logger.error(f"is account exsit failed because of Non user id")
                return False
        except Exception as ex:
            logger.error(f"is account exsit  failed with error {ex}")

    def isMemberExist(self, member_id):
        query = "select * from player where player_id = ?"
        try:
            value = (member_id,)
            self.cursor.execute(query, value)
            result = self.cursor.fetchone()

            return result is not None
        except Exception as ex:
            logger.error(f"isMemberExist has failed with error {ex}")

    def get_players(self):
        query = """
            select p.player_id, p.game_name, p.tag_id
            from player p
            left join playerGameDetail g on p.player_id = g.player_id
            where g.player_id is null           
            """
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(f"get_player has failed with error {ex}")

    def remove_player(self, member_id):
        query = "delete from player where player_id = ?"
        try:
            value = (member_id,)
            self.cursor.execute(query, value)
            self.connection.commit()
        except Exception as ex:
            logger.error(f"unable to delete a player_id {member_id} from db with error {ex}")

    def metadata(self):
        query = "PRAGMA table_info(player)" 
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(f"metadata has failed with error {ex}")
    
    def generalplayerQuery(self, query, values):
        try:
            self.cursor.execute(query, values)
            self.connection.commit()
        except Exception as ex:
            logger.error(f"generalplayerQuery has failed with error {ex}")

class Player_game_info(Tournament_DB):
    
    def createTable(self):

        game_table_query = """
            CREATE TABLE IF NOT EXISTS playerGameDetail (
            player_gamedetail integer primary key autoincrement,
            player_id bigint,
            tier text,
            rank text,
            role text,
            wins integer integer default 0,
            losses integer integer default 0,
            wr float generated always as (wins * 1.0 / (wins + losses)) stored,
            participation integer integer default 0,
            toxicity integer integer default 0,
            mvps integer,
            isPromoted integer default 0,
            isDEMOTION integer default 0,
            totalPoint integer default 0,
            game_played integer generated always as (wins + losses) stored,
            last_modified text default (datetime('now')),
            FOREIGN KEY (player_id) REFERENCES player (player_id) ON DELETE CASCADE
        )
        """
        self.cursor.execute(game_table_query)
        self.connection.commit()

    def update_pref(self, interaction, pref):
        register_query = """
            UPDATE playerGameDetail
            SET role = ?
            WHERE player_id = ?;
            """
        pref = json.dumps(pref)
        try:
            uniq_player_id = interaction.user.id
            if uniq_player_id:
                self.cursor.execute(register_query, (pref, uniq_player_id))
                self.connection.commit()
            else:
                logger.error(f"update_role ahs failed because of Non user id")
        except Exception as ex:
            logger.error(f"update_role has failed with error {ex}")

    def update_player_API_info(self, player_id, tier, rank, wins, losses):
        register_query = "insert or replace into playerGameDetail (player_id, tier, rank, wins, losses) values(?, ?, ?, ?, ?)"
        try:
            self.cursor.execute(register_query, (player_id, tier, rank, wins, losses))
            self.connection.commit()
            
        except Exception as ex:
            logger.error(f"update_player_API_info {player_id} has failed with error {ex}")

    def fetchGameDetails(self):
        query = "select player_id, tier, rank, role, wr from playerGameDetail"
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(f"fetchGameDetails has failed with error {ex}")

    def fetch_for_tier_promotion(self):
        query = "select player_id, tier, game_played, wr from playerGameDetail"
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(f"fetch_for_tier_promotion has failed with error {ex}")
    
    def fetch_by_id(self, player_id):
        query = "select tier from playerGameDetail where player_id = ?"
        try:
            self.cursor.execute(query, (player_id,))
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(f"fetch_by_id has failed with error {ex}")

    
    def update_tier(self, player_id, tier):
        update_query = "update playerGameDetail set tier = ? where player_id = ?"
        try:
            self.cursor.execute(update_query, (tier, player_id))
            self.connection.commit()
        except Exception as ex:
            logger.error(f"update_tier has failed with error {ex}")

    def giveaway_top(self, top):
        query = """
            SELECT pg.player_id, p.user_name
            FROM playerGameDetail AS pg
            JOIN player AS p ON pg.player_id = p.player_id
            ORDER BY pg.totalPoint DESC
            LIMIT ?
        """
        try:
            self.cursor.execute(query, (top, ))
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(f"check_in has failed with error {ex}")

    def for_giveaway(self, top):
            query = """
                SELECT pg.player_id, p.user_name 
                FROM playerGameDetail AS pg
                JOIN player AS p ON pg.player_id = p.player_id
                ORDER BY pg.totalPoint DESC
                LIMIT 999999 OFFSET ?
            """
            try:
                self.cursor.execute(query, (top, ))
                return self.cursor.fetchall()
            except Exception as ex:
                logger.error(f"check_in has failed with error {ex}")

    def exportToGoogleSheet(self):
            query = """
                SELECT pg.player_id, p.user_name, pg.tier, pg.rank, pg.role, pg.wins, pg.losses, pg.wr, pg.game_played, pg.participation, pg.toxicity, pg.totalPoint, pg.isPromoted, pg.isDEMOTION
                FROM playerGameDetail AS pg
                JOIN player AS p ON pg.player_id = p.player_id
            """
            try:
                self.cursor.execute(query)
                headers = [desc[0] for desc in self.cursor.description]
                result =  self.cursor.fetchall()
                return headers, result
            except Exception as ex:
                logger.error(f"exportToGoogleSheet has failed with error {ex}")

    def importToDb(self, query, values):
            try:
                self.cursor.execute(query, values)
                self.connection.commit()
            except Exception as ex:
                logger.error(f"exportToGoogleSheet has failed with error {ex}")

    def metadata(self):
        query = "PRAGMA table_info(playerGameDetail)" 
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(f"metadata has failed with error {ex}")

    def isExistPlayerId(self, query, query_param):
        try:
            self.cursor.execute(query, query_param)
            result = self.cursor.fetchone()[0]
            return result
            
        except Exception as ex:
            logger.error(f"is account exsit  failed with error {ex}")

class Checkin(Tournament_DB):

    def createTable(self):

        checkin_table_query = """
            CREATE TABLE IF NOT EXISTS checkin (
            checkin_id integer primary key autoincrement,
            player_id bigint,
            player_gamedetail integer,
            isParticipant integer default 0,
            FOREIGN KEY (player_id) REFERENCES player (player_id),
            FOREIGN KEY (player_gamedetail) REFERENCES playerGameDetail (player_gamedetail)
        )
        """
        self.cursor.execute(checkin_table_query)
        self.connection.commit()

    def check_in(self, interaction):
        register_query = """
            insert or replace into checkin(player_id, player_gamedetail)
            select p.player_id, g.player_gamedetail
            from player p
            join playerGameDetail g on p.player_id = g.player_id
            where p.player_id = ?
            """

        try:
            uniq_player_id = interaction.user.id
            if uniq_player_id:
                self.cursor.execute(register_query, (uniq_player_id,))
                self.connection.commit()
            else:
                logger.error(f"check_in ahs failed because of Non user id")
        except Exception as ex:
            logger.error(f"check_in has failed with error {ex}")

    def seat_out(self, player_id):
        query = "update checkin set isParticipant = 1 where player_id = ?"
        try:
            value = (player_id,)
            self.cursor.execute(query, value)
            self.connection.commit()
        except Exception as ex:
            logger.error(f"seat_out has failed with error {ex}")

    def remove_player(self, player_id):
        query = "delete from checkin where player_id = ?"
        try:
            value = (player_id,)
            self.cursor.execute(query, value)
            self.connection.commit()
        except Exception as ex:
            logger.error(f"unable to delete a player_id {player_id} from db with error {ex}")

    def fetch_for_match(self):
        query = """
            select p.player_id, p.user_name, g.tier, g.rank, g.wr, g.role, c.isParticipant
            from checkin c
            join player p on c.player_id = p.player_id
            join playerGameDetail g on c.player_id = g.player_id
            where c.isParticipant = 0
        """
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(f"fetch_for_match has failed with error {ex}")
    
    def clear_checkin(self):
        query = "delete from checkin"
        try:
            self.cursor.execute(query)
            self.connection.commit()
        except Exception as ex:
            logger.error(f"clear_checkin has failed with error {ex}")

class TeamList(Tournament_DB):
    
    def createTable(self):

        teamlist_table_query = """
            CREATE TABLE IF NOT EXISTS team_list (
            team_id integer primary key autoincrement,
            teamName text unique,
            win integer default 0,
            loss integer default 0,
            pool_id text
        )
        """
        self.cursor.execute(teamlist_table_query)
        self.connection.commit()

class GameDetails(Tournament_DB):
    
    def createTable(self):

        match_table_query = """
            CREATE TABLE IF NOT EXISTS game_detail (
            id integer primary key autoincrement,
            checkin_id integer,
            teamName text,
            assigned_role text,
            FOREIGN KEY (teamName) REFERENCES team_list (teamName),
            FOREIGN KEY (checkin_id) REFERENCES checkin (checkin_id)
        )
        """
        self.cursor.execute(match_table_query)
        self.connection.commit()