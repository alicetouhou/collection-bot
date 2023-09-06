import requests
import json
from html.parser import HTMLParser
import re
import csv
import math
import psycopg2
import math
import random

f = open('token.json')
data = json.load(f)
token = data['access_token']
HEADERS = { "Authorization" : f"Bearer {token}" }

class Character:
    first_name = ""
    last_name = ""
    anime = ""
    manga = ""
    game = ""
    images = []
    favorites = 0
    value = 0
    id = 0

    def __init__(self, first_name=first_name, last_name=last_name, anime=anime, images=images, id=id, favorites=favorites, manga=manga, game=game):
        self.first_name = first_name.replace("&#039;","'")
        self.last_name = last_name
        self.anime = anime
        self.manga = manga
        self.game = game
        self.images = images
        self.id = id
        self.favorites = favorites
        self.value = self.get_value()

    def __str__(self):
        return f'ID: {self.id}, First name: {self.first_name}, Last name: {self.last_name}, Anime: {self.anime}, Value: {self.value}, Images: {len(self.images)}'
    
    def get_value(self) -> int:
        if int(self.favorites) > 0:
            value = max(math.floor(200 * math.log(int(self.favorites), 10) - 100),15)
            if value == 15:
                return int(math.pow(random.random(), 3) * 22 + 15)
            return value
        return 10
    
    def get_images_str(self) -> str:
        return ",".join(self.images)

class Series:
    id = 0
    title = ""

    def __init__(self, id = id, title = title):
        self.id = id
        self.title = title

class CharacterParser(HTMLParser):
    id_list = []
    favorites_list = []
    def handle_starttag(self, tag, attrs) -> None:
        if tag == 'a':
            for i in attrs:
                if "myanimelist.net/character" in i[1]:
                    m = re.search('character\/(\d+)\/', i[1])
                    if m is None:
                        return
                    if not m.groups()[0] in self.id_list:
                        self.id_list.append(m.groups()[0])

    def handle_data(self, data: str) -> None:
        if " Favorites" in data:
            m = re.search('([1234567890,]+) Favorites', data)
            if m is None:
                return
            self.favorites_list.append(m.groups()[0].replace(",",""))

def get_top_anime_ids(amount, offset, type="anime"):
    x = requests.get(f'https://api.myanimelist.net/v2/{type}/ranking?ranking_type=bypopularity&limit={amount}&offset={offset}', headers = HEADERS)
    anime_json = json.loads(x.text)

    output = []
    for anime in anime_json['data']:
        output.append(Series(id=anime['node']['id'], title=anime['node']['title']))

    return output

def get_series_by_ids(ids: list[int], type="anime"):
    output = []
    for id in ids:
        x = requests.get(f'https://api.myanimelist.net/v2/{type}/{id}', headers = HEADERS)
        series_json = json.loads(x.text)
        output.append(Series(id=series_json['id'], title=series_json['title']))
    return output


def get_anime_characters(anime: Series, type="anime", game_override="",favorites_scale=1):
    character_list = []
    anime_html = requests.get(f'https://myanimelist.net/{type}/{anime.id}/x/characters')
    parser = CharacterParser()
    parser.id_list = []
    parser.favorites_list = []
    parser.feed(anime_html.text)
    parser.close()
    parser.id_list = parser.id_list[:len(parser.id_list)-5]
    print(f"Now Grabbing: {anime.id} - {anime.title}")

    for index,character_id in enumerate(parser.id_list):
        favorites = "0"
        if len(parser.favorites_list) > index:
            favorites = parser.favorites_list[index]
        else:
            favorites = "0"
        
        if favorites != "0":
            favorites = int(favorites) * favorites_scale
            try:
                char_request = requests.get(f' https://api.myanimelist.net/v2/characters/{character_id}?fields=first_name,last_name,pictures',headers = HEADERS)
                char_json = json.loads(char_request.text)

                if "pictures" in char_json:
                    pictures = []
                    for value in char_json["pictures"]:
                        pictures.append(value["medium"])
                    if type == "anime":
                        new_character = Character(id=character_id, first_name=char_json["first_name"], last_name=char_json["last_name"], anime=anime.title, manga="", game=game_override, images=pictures, favorites=favorites)
                    elif type == "manga":
                        new_character = Character(id=character_id, first_name=char_json["first_name"], last_name=char_json["last_name"], anime="", manga=anime.title, game=game_override, images=pictures, favorites=favorites)
                    print(new_character)
                    character_list.append(new_character)
            except(json.decoder.JSONDecodeError):
                pass


    parser.id_list = []
    parser.favorites_list = []
    parser.reset()

    return character_list
        
def save_to_db(database, character_list: list[Character], type="anime") -> None:
    cursor = database.cursor()
    for character in character_list:
        if type == "anime":
            cursor.execute("SELECT anime_list FROM CHARACTERS WHERE ID = %(id)s", {"id" : character.id})
            old_anime_list = cursor.fetchone()
            if not old_anime_list is None and not character.anime in old_anime_list[0]:
                new_anime_list = old_anime_list[0] + "," + character.anime
                cursor.execute("UPDATE CHARACTERS SET anime_list = %(newlist)s WHERE ID = %(id)s", {"id" : character.id, "newlist" : new_anime_list})
            sql = """INSERT INTO CHARACTERS VALUES (%(id)s,%(first_name)s,%(last_name)s,%(anime)s,%(images)s,%(value)s,%(manga)s,%(games)s) ON CONFLICT DO NOTHING"""
            cursor.execute(sql, {"id" : character.id, "first_name" : character.first_name, "last_name" : character.last_name, "anime" : character.anime, "images" : character.get_images_str(), "value" : character.get_value(), "manga" : "", "games" : ""})

        if type == "manga":
            cursor.execute("SELECT manga_list FROM CHARACTERS WHERE ID = %(id)s", {"id" : character.id})
            old_manga_list = cursor.fetchone()
            if not old_manga_list is None and not character.manga in old_manga_list[0]:
                new_manga_list = old_manga_list[0] + "," + character.manga
                cursor.execute("UPDATE CHARACTERS SET manga_list = %(newlist)s WHERE ID = %(id)s", {"id" : character.id, "newlist" : new_manga_list})
            sql = """INSERT INTO CHARACTERS VALUES (%(id)s,%(first_name)s,%(last_name)s,%(anime)s,%(images)s,%(value)s,%(manga)s,%(games)s) ON CONFLICT DO NOTHING"""
            cursor.execute(sql, {"id" : character.id, "first_name" : character.first_name, "last_name" : character.last_name, "anime" : "", "images" : character.get_images_str(), "value" : character.get_value(), "manga" : character.manga, "games" : ""})

        if type == "game":
            cursor.execute("SELECT games_list FROM CHARACTERS WHERE ID = %(id)s", {"id" : character.id})
            sql = """INSERT INTO CHARACTERS VALUES (%(id)s,%(first_name)s,%(last_name)s,%(anime)s,%(images)s,%(value)s,%(manga)s,%(games)s) ON CONFLICT DO NOTHING"""
            cursor.execute(sql, {"id" : character.id, "first_name" : character.first_name, "last_name" : character.last_name, "anime" : "", "images" : character.get_images_str(), "value" : character.get_value(), "manga" : "", "games" : character.game})

    outputquery = "COPY ({0}) TO STDOUT WITH DELIMITER '|' CSV HEADER".format("SELECT * FROM CHARACTERS")
    with open('bot\data\db.csv', 'w', encoding="utf-8") as f:
        cursor.copy_expert(outputquery, f)

    database.commit()
    cursor.close()

def main():
    database = psycopg2.connect(database="characters",
                        host="localhost",
                        user="postgres",
                        password="",
                        port="5432")

    cursor = database.cursor()

    #cursor.execute("DROP TABLE IF EXISTS CHARACTERS")
    cursor.execute("CREATE TABLE IF NOT EXISTS CHARACTERS(ID int, first_name varchar(255), last_name varchar(255), anime_list varchar(1027), pictures varchar(2055), value int, manga_list varchar(1027), games_list varchar(1027), PRIMARY KEY (ID))")

    #extras = [48651]
    #anime_list = get_series_by_ids(extras,type="anime")
    anime_list = get_top_anime_ids(31,569,type="anime")
    for anime in anime_list:
        characters = get_anime_characters(anime,type="anime")
        save_to_db(database, characters,type="anime")

    # manga_list = [86918]
    # manga_list = get_series_by_ids(manga_list,type="manga")
    # for manga in manga_list:
    #     characters = get_anime_characters(manga,type="manga")
    #     save_to_db(database, characters,type="manga")

    # games_list_a = [51105]
    # games_list_m = []

    # games_list_a = get_series_by_ids(games_list_a,type="anime")
    # game_name = "NieR:Automata"
    # for game in games_list_a:
    #     characters = get_anime_characters(game,type="anime",game_override=game_name,favorites_scale=2)
    #     save_to_db(database, characters,type="game")

if __name__ == "__main__":
    main()