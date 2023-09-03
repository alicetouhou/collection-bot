import crescent
import hikari
import psycopg2
import bot.dbpool

from bot.model import Model
from bot.character import Character

Plugin = crescent.Plugin[hikari.GatewayBot, Model]

def add_player_to_db(guild: int, id: int):
    guild_str = f"players_{guild}"
    with bot.dbpool.db_cursor() as cur:
        cur.execute(f"INSERT INTO {guild_str} VALUES (%(id)s,'',%(currency)s,0,0) ON CONFLICT DO NOTHING", {"id": str(id), "currency": 0}) 

def pick_random_character() -> Character:
    with bot.dbpool.db_cursor() as cur:
        cur.execute("""SELECT * FROM CHARACTERS
                        ORDER BY RANDOM()
                        LIMIT 1""")
        data = cur.fetchone()
        return Character(data)
    
def claim_character(guild: int, id: int, character: Character) -> None:
    guild_str = f"players_{guild}"
    add_player_to_db(guild, id)
    with bot.dbpool.db_cursor() as cur:
        cur.execute(f"SELECT characters FROM {guild_str} WHERE ID = %(id)s", {"id": str(id)})
        old_list = cur.fetchone()
        if not old_list is None:
            new_list = old_list[0] + "," + str(character.id)
            cur.execute(f"UPDATE {guild_str} SET characters = %(newlist)s WHERE ID = %(id)s", {"id": str(id), "newlist" : new_list})

def get_characters(guild: int, id: int) -> list[Character]:
    guild_str = f"players_{guild}"
    add_player_to_db(guild, id)
    with bot.dbpool.db_cursor() as cur:
        cur.execute(f"SELECT characters FROM {guild_str} WHERE ID = %(id)s", {"id": str(id)})
        character_str = cur.fetchone()[0]
        character_ids_list = character_str.split(",")
        character_list = []
        for char_id in character_ids_list:
            if char_id != '':
                cur.execute("""SELECT * FROM CHARACTERS WHERE ID = %(id)s""", {"id" : int(char_id)})
                data = cur.fetchone()
                character_list.append(Character(data))
        return character_list

def get_daily_claimed_time(guild: int, id: int) -> int:
    guild_str = f"players_{guild}"
    add_player_to_db(guild, id)
    with bot.dbpool.db_cursor() as cur:
        cur.execute(f"SELECT claimed_daily FROM {guild_str} WHERE ID = %(id)s", {"id": str(id)})
        return cur.fetchone()[0]
    
def set_daily_claimed_time(guild: int, id: int, time: int) -> None:
        guild_str = f"players_{guild}"
        add_player_to_db(guild, id)
        with bot.dbpool.db_cursor() as cur:
            cur.execute(f"UPDATE {guild_str} SET claimed_daily = %(time)s WHERE ID = %(id)s", {"id": str(id), "time" : time})

def get_claims(guild: int, id: int) -> int:
    guild_str = f"players_{guild}"
    add_player_to_db(guild, id)
    with bot.dbpool.db_cursor() as cur:
        cur.execute(f"SELECT claims FROM {guild_str} WHERE ID = %(id)s", {"id": str(id)})
        return cur.fetchone()[0]
    
def add_claims(guild: int, id: int, number: int) -> None:
    guild_str = f"players_{guild}"
    add_player_to_db(guild, id)
    with bot.dbpool.db_cursor() as cur:
        cur.execute(f"SELECT claims FROM {guild_str} WHERE ID = %(id)s", {"id": str(id)})
        old_amount = cur.fetchone()
        if not old_amount is None:
            new_amount = old_amount[0] + number
            cur.execute(f"UPDATE {guild_str} SET claims = %(amount)s WHERE ID = %(id)s", {"id": str(id), "amount" : new_amount})

def search_characters(id: str or None, first_name: str or None, last_name: str or None, appearences: str or None):
    with bot.dbpool.db_cursor() as cur:
        sql = "SELECT * FROM CHARACTERS "

        if id: sql += "AND ID = %(id)s "
        if first_name: sql += "AND LOWER(first_name) = LOWER(%(first_name)s) "
        if last_name: sql += "AND LOWER(anime_list) LIKE LOWER(%(appearences)s) "
        if appearences: sql += "AND LOWER(first_name) = LOWER(%(first_name)s) "
        sql = sql.replace("AND", "WHERE", 1)

        cur.execute(sql, {"id" : id, "first_name": first_name, "last_name": last_name, "appearences": appearences})
        characters = cur.fetchall()

        character_list = []
        for char in characters:
            character_list.append(Character(char))

        return character_list