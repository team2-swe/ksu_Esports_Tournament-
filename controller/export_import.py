import discord
from datetime import datetime
from discord import app_commands
from discord.ext import commands
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import settings
from model.dbc_model import Tournament_DB ,Player, Player_game_info

scopes = ['https://www.googleapis.com/auth/spreadsheets']
logger = settings.logging.getLogger("discord")

class Import_Export(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spreadsheets_service = self.sheet_service()
        self.googleSheetId = settings.GOOGLE_SHEET_ID

    '''A method to get the spreedsheet service
    '''
    def sheet_service(self):
        credentials = service_account.Credentials.from_service_account_file(
            filename=settings.LOL_service_path, scopes=scopes
        )
        serviceSheet = build('sheets', 'v4', credentials=credentials)

        spreadsheets_service = serviceSheet.spreadsheets()

        return spreadsheets_service
    
    #Method to check if a sheet exists, returns True/False
    def isSheetExists(self, sheet_name):
        spreadsheet = self.spreadsheets_service.get(spreadsheetId=self.googleSheetId).execute()
        sheets = spreadsheet.get('sheets', [])

        for sheet in sheets:
            if sheet['properties']['title'] == sheet_name:
                return True
        return False
    
    '''Method to create a sheet with the name passed in and a bool to clear the sheet if it already exists
        steps:
            Check if the sheet name already exist, 
                if not then create it 
                    Call the API to add a new sheet
                    Get the new sheet's ID from the response and return the value
                if exist then check if the clear parm is True to delete the data
    '''
    async def sheets_create(self, sheet_name, clear):
        if not self.isSheetExists(sheet_name):
            request_body = {'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}

            response = self.spreadsheets_service.batchUpdate(spreadsheetId=self.googleSheetId, body=request_body).execute()

            return response['replies'][0]['addSheet']['properties']['sheetId']
        
        elif clear:
            range_to_clear = f'{sheet_name}'

            request_body = {}
            self.spreadsheets_service.values().clear(spreadsheetId=self.googleSheetId,range=range_to_clear,body=request_body).execute()

        # Get the sheet ID from the sheet name by looping through each sheet until it matches
        spreadsheet = self.spreadsheets_service.get(spreadsheetId=self.googleSheetId).execute()
        sheets = spreadsheet.get('sheets', [])
        for sheet in sheets:
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
    
    '''Method to export the points data from the database to the sheet
        steps:
            check if the sheet exists, if yes clear it out
            get playeres data based on model 'exportToGoogleSheet' then:
                Convert fetched data to a list of lists suitable for Google Sheets
                update into googlesheet
            defer the responce to make sure no time out error
    '''  
    @app_commands.command(name="export_players", description="export all playeres information")  
    async def exportToGoogleSheet(self, interaction:discord.Interaction):

        if interaction.user.guild_permissions.administrator:
            today = datetime.now()
            sheet_name = f"players_{str(today.strftime('%m%d%Y'))}"
            await self.sheets_create(sheet_name, True)
            
            try:
                await interaction.response.defer()

                db = Tournament_DB()
                header, list_of_playeres = Player_game_info.exportToGoogleSheet(db)
                db.close_db()

                data = [list(map(str, row)) for row in list_of_playeres]

                data.insert(0, header)

                start_cell = 'A1'
                end_cell = f'{chr(ord("A") + len(data[0]) - 1)}{len(data)}'
                range_name = f'{sheet_name}!{start_cell}:{end_cell}'

                body = {'values': data}
                self.spreadsheets_service.values().update(spreadsheetId=self.googleSheetId,range=range_name,valueInputOption='RAW',body=body).execute()
                sheet_url = sheet_url = f"https://docs.google.com/spreadsheets/d/{self.googleSheetId}/edit"
                # await interaction.response.send_message("sucessfully created googlesheet")
                await interaction.followup.send(f"✅ Google Sheet Created! [Click Here]({sheet_url})")

            except Exception as e:
                print (f'Export has error: {e}')
        else:
            await interaction.response.send_message(f"Sorry you dont have access to use this command",
                                                        ephemeral=True)



    '''Method to import playeres data from googlesheet to db
        Steps:
            pass a sheet_name with the command or configure in .env, else it takes a defult name one 'sheet'
            get the headere and row data from sheet_name
            get colums name from 'playerGameDetail' table
            add player information to db accordingly
    '''
    @app_commands.command(name="import_players", description="sheet_name can be configured in .dev file")
    async def importFromGoogleSheet(self, interaction:discord.Interaction, sheet_name: str = settings.CELL_RANGE):
        if interaction.user.guild_permissions.administrator:
            try:
                await interaction.response.defer()
                sheet_data = self.spreadsheets_service.values().get(
                    spreadsheetId=self.googleSheetId, range=sheet_name
                ).execute()

                values = sheet_data.get("values", [])

                if not values:
                    print("No data found in the Google Sheet.")
                    exit()

                # headers = values[0]
                headers = [header.strip() for header in values[0]]

                rows = values[1:]
                db = Tournament_DB()

                '''table_columns is the player game details column name
                    Find matching columns (ignore extra columns in Google Sheets)
                '''
                table_columns = Player_game_info.metadata(db)
                table_columns = {row[1]: row[1] for row in table_columns}  
                valid_columns = [col for col in headers if col in table_columns]

                ''' this is fro player table
                    Find matching columns (ignore extra columns in Google Sheets)
                '''
                player_columns = Player.metadata(db)
                p_table_columns = {row[1]: row[1] for row in player_columns}
                p_valid_columns = [col for col in headers if col in p_table_columns]
                

                # Process Each Row and Update DB
                for row in rows:
                    # Convert row into {header: value} format
                    row_data = dict(zip(headers, row))

                    columns_to_update = []
                    values_to_insert = []

                    p_columns_to_update = []
                    p_values_to_insert = []
                    
                    values_to_insert = [row_data.get(col, None) for col in valid_columns]
                    p_values_to_insert = [row_data.get(col, None) for col in p_valid_columns]

                    if "player_id" in row_data:
                        '''first we need to check if player_id is exist in player table
                            if not exist insert a player data in player table
                        '''
                        sql_query = f"""
                            INSERT INTO player ({', '.join(p_valid_columns)}) 
                            VALUES ({', '.join(['?' for _ in p_valid_columns])}) 
                            ON CONFLICT(player_id) DO UPDATE SET 
                            {', '.join([f"{col} = EXCLUDED.{col}" for col in p_valid_columns if col != 'player_id'])};
                        """
                        Player.generalplayerQuery(db, sql_query, p_values_to_insert)

                        
                        '''After the player table is updated update playerGameDetail
                        '''
                        column_names = ', '.join(valid_columns)
                        placeholders = ', '.join(['?' for _ in valid_columns])
                        query = "SELECT COUNT(*) FROM playerGameDetail WHERE player_id = ?"
                        query_params = (row_data["player_id"],)

                        isExistPlayerId = Player_game_info.isExistPlayerId(db, query=query, query_param=query_params)

                        if isExistPlayerId:
                            update_query = f"""
                                UPDATE playerGameDetail
                                SET {', '.join([f"{col} = ?" for col in valid_columns if col != 'player_id'])}
                                WHERE player_id = ?;
                            """
                            Player_game_info.importToDb(db, update_query, [row_data[col] for col in valid_columns if col != 'player_id'] + [row_data["player_id"]])
                        else:
                            insert_query = f"""
                                INSERT INTO playerGameDetail ({column_names}) 
                                VALUES ({placeholders});
                            """
                            Player_game_info.importToDb(db, insert_query, [row_data[col] for col in valid_columns])

                db.close_db()
                await interaction.followup.send("✅ Data Imported and Updated Successfully!")
            except Exception as ex:
                logger.info(f"import has an error, please check the googlesheet data")

        else:
            await interaction.response.send_message(f"Sorry you dont have access to use this command",
                                                        ephemeral=True)
        

async def setup(bot):
    await bot.add_cog(Import_Export(bot))