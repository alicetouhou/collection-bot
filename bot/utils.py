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
        cur.execute(f"INSERT INTO {guild_str} VALUES (%(id)s,'',%(currency)s,0,0,10,0,'','') ON CONFLICT DO NOTHING", {"id": str(id), "currency": 0}) 

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

def remove_character(guild: int, id: int, character: Character) -> None:
    guild_str = f"players_{guild}"
    add_player_to_db(guild, id)
    with bot.dbpool.db_cursor() as cur:
        cur.execute(f"SELECT characters FROM {guild_str} WHERE ID = %(id)s", {"id": str(id)})
        old_list = cur.fetchone()
        if not old_list is None:
            new_list = old_list[0].split(",")
            new_list.remove(str(character.id))
            new_list = ",".join(new_list)
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
    
def is_claimed(guild: int, character: Character) -> bool:
    guild_str = f"players_{guild}"
    with bot.dbpool.db_cursor() as cur:
        cur.execute(f"SELECT characters FROM {guild_str}")
        lists = cur.fetchall()
        list = []
        for i in lists:
            current_list = i[0].split(",")
            list += current_list
        return character in list

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

def get_daily_rolls_time(guild: int, id: int) -> int:
    guild_str = f"players_{guild}"
    add_player_to_db(guild, id)
    with bot.dbpool.db_cursor() as cur:
        cur.execute(f"SELECT claimed_rolls FROM {guild_str} WHERE ID = %(id)s", {"id": str(id)})
        return cur.fetchone()[0]
    
def set_daily_rolls_time(guild: int, id: int, time: int) -> None:
        guild_str = f"players_{guild}"
        add_player_to_db(guild, id)
        with bot.dbpool.db_cursor() as cur:
            cur.execute(f"UPDATE {guild_str} SET claimed_rolls = %(time)s WHERE ID = %(id)s", {"id": str(id), "time" : time})

def get_rolls(guild: int, id: int) -> int:
    guild_str = f"players_{guild}"
    add_player_to_db(guild, id)
    with bot.dbpool.db_cursor() as cur:
        cur.execute(f"SELECT rolls FROM {guild_str} WHERE ID = %(id)s", {"id": str(id)})
        return cur.fetchone()[0]
    
def add_rolls(guild: int, id: int, number: int) -> None:
    guild_str = f"players_{guild}"
    add_player_to_db(guild, id)
    with bot.dbpool.db_cursor() as cur:
        cur.execute(f"SELECT rolls FROM {guild_str} WHERE ID = %(id)s", {"id": str(id)})
        old_amount = cur.fetchone()
        if not old_amount is None:
            new_amount = old_amount[0] + number
            cur.execute(f"UPDATE {guild_str} SET rolls = %(amount)s WHERE ID = %(id)s", {"id": str(id), "amount" : new_amount})

def get_currency(guild: int, id: int) -> int:
    guild_str = f"players_{guild}"
    add_player_to_db(guild, id)
    with bot.dbpool.db_cursor() as cur:
        cur.execute(f"SELECT currency FROM {guild_str} WHERE ID = %(id)s", {"id": str(id)})
        return cur.fetchone()[0]
    
def add_currency(guild: int, id: int, number: int) -> None:
    guild_str = f"players_{guild}"
    add_player_to_db(guild, id)
    with bot.dbpool.db_cursor() as cur:
        cur.execute(f"SELECT currency FROM {guild_str} WHERE ID = %(id)s", {"id": str(id)})
        old_amount = cur.fetchone()
        if not old_amount is None:
            new_amount = old_amount[0] + number
            cur.execute(f"UPDATE {guild_str} SET currency = %(amount)s WHERE ID = %(id)s", {"id": str(id), "amount" : new_amount})


def search_characters(id: str or None, name: str or None, appearences: str or None, limit: int=0, fuzzy: bool=False) -> list[Character]:
    with bot.dbpool.db_cursor() as cur:
        first_name = None
        last_name = None
        if name:
            first_name = name
            last_name = None
            names = name.split(" ")
            if len(names) > 1:
                first_name = " ".join(names[0:len(names)-1])
                last_name = names[len(names)-1]

        sql = "SELECT * FROM CHARACTERS "

        if id: sql += "AND ID = %(id)s "
        if first_name: sql += "AND LOWER(first_name) = LOWER(%(first_name)s) "
        if last_name: sql += "AND LOWER(last_name) = LOWER(%(last_name)s) "

        if fuzzy == True:
            first_name = "%" + first_name + "%" if first_name else None
            last_name = "%" + last_name + "%" if last_name else None
            sql = sql[::-1].replace("=", "EKIL", 2)[::-1]

        
        if appearences: 
            appearences = "%" + appearences + "%"
            sql += "AND (LOWER(anime_list) LIKE LOWER(%(appearences)s) OR LOWER(manga_list) LIKE LOWER(%(appearences)s) OR LOWER(games_list) LIKE LOWER(%(appearences)s))"
        sql += "ORDER BY first_name "
        sql = sql.replace("AND", "WHERE", 1)
        if limit > 0: sql += f"LIMIT {limit}"

        cur.execute(sql, {"id" : id, "first_name": first_name, "last_name": last_name, "appearences": appearences})
        characters_a = cur.fetchall()

        characters_b = []
        if first_name != None:
            sql = sql.replace("first_name", "temp_name")
            sql = sql.replace("last_name", "first_name")
            sql = sql.replace("temp_name", "last_name")
            cur.execute(sql, {"id" : id, "first_name": last_name, "last_name": first_name, "appearences": appearences})
            characters_b = cur.fetchall()

        character_list = []
        for char in characters_a:
            character_list.append(Character(char))
        for char in characters_b:
            character_list.append(Character(char))

        return character_list