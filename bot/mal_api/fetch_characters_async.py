import pandas
import asyncio
import aiohttp
import os
import dotenv
import typing as t
import json
from bs4 import BeautifulSoup
import re
import math
import random
import progressbar
from time import sleep
import io
import imagesize

dotenv.load_dotenv()

token = os.environ["MAL_ACCESS_TOKEN"]
HEADERS = {"Authorization": f"Bearer {token}"}

characters_csv = pandas.read_csv("bot/data/characters.csv",
                                 header=0, delimiter="|", encoding="utf8")
series_csv = pandas.read_csv("bot/data/series.csv",
                             header=0, delimiter="|", encoding="utf8")
series_correspondences_csv = pandas.read_csv("bot/data/series_correspondences.csv",
                                             header=0, delimiter="|", encoding="utf8")

images_correspondences_csv = pandas.read_csv("bot/data/images_correspondences.csv",
                                             header=0, delimiter="|", encoding="utf8")

buckets_csv = pandas.read_csv("bot/data/buckets.csv",
                              header=0, delimiter="|", encoding="utf8")


class Series:
    id = 0
    title = ""

    def __init__(self, id=id, title=title):
        self.id = id
        self.title = title


class Character:
    first_name = ""
    last_name = ""
    anime = ""
    manga = ""
    game = ""
    images: list[str] = []
    favorites = 0
    value = 0
    id = 0

    def __init__(
        self,
        first_name=first_name,
        last_name=last_name,
        anime=anime,
        images=images,
        id=id,
        favorites=favorites,
        manga=manga,
        game=game,
    ):
        self.first_name = first_name.replace("&#039;", "'")
        self.last_name = last_name
        self.anime = anime
        self.manga = manga
        self.game = game
        self.images = images
        self.id = id
        self.favorites = favorites
        self.value = self.get_value()

    def __str__(self):
        return f"ID: {self.id}, First name: {self.first_name}, Last name: {self.last_name}, Anime: {self.anime}, Value: {self.value}, Images: {len(self.images)}"

    def get_value(self) -> int:
        if int(self.favorites) > 0:
            value = max(math.floor(
                200 * math.log(int(self.favorites), 10) - 100), 15)
            if value == 15:
                return int(math.pow(random.random(), 3) * 22 + 15)
            if value == 10:
                return int(math.pow(random.random(), 3) * 11 + 10)
            return value
        return 10

    def get_images_str(self) -> str:
        return ",".join(self.images)


async def get_series_from_ids(session: aiohttp.ClientSession, ids: list[int], type) -> list[Series]:
    output = []
    for id in ids:
        url = f'https://api.myanimelist.net/v2/{type}/{id}'
        async with session.get(url=url, headers=HEADERS) as response:
            resp = await response.read()
            anime = json.loads(resp)

            output.append(
                Series(id=anime["id"], title=anime["title"]))

    return output


async def get_top_series_ids(session: aiohttp.ClientSession, amount, offset, type) -> list[Series]:
    url = f'https://api.myanimelist.net/v2/{type}/ranking?ranking_type=bypopularity&limit={amount}&offset={offset}'
    async with session.get(url=url, headers=HEADERS) as response:
        resp = await response.read()
        anime_json = json.loads(resp)

        print(anime_json)

        output = []
        for anime in anime_json["data"]:
            output.append(
                Series(id=anime["node"]["id"], title=anime["node"]["title"]))

    return output


async def get_character(session: aiohttp.ClientSession, character_id: int):
    url = f"https://api.myanimelist.net/v2/characters/{character_id}?fields=first_name,last_name,pictures"
    async with session.get(url=url, headers=HEADERS) as response:
        resp = await response.json()
        return resp


async def get_characters_in_series(session: aiohttp.ClientSession, series: Series, type: str, index: int = 0) -> list[Character]:
    url = f"https://myanimelist.net/{type}/{series.id}/x/characters"
    async with session.get(url=url) as response:
        resp = await response.read()

        output_characters = []
        character_array = []

        soup = BeautifulSoup(resp, 'html.parser')

        print(f"Now grabbing: {series.title} ({type}) ({index})")

        data = soup.find_all('td', class_='borderClass bgColor2')
        data += soup.find_all('td', class_='borderClass bgColor1')
        for datapiece in data:
            datastring = str(datapiece)
            if "myanimelist.net/character" in datastring:
                m = re.search("character\/(\d+)\/", datastring)
                n = re.search("([1234567890,]+) Favorites", datastring)
                if m and n:
                    character_array.append(
                        [int(m.groups()[0]), int(n.groups()[0].replace(",", ""))])

        for character_piece in progressbar.progressbar(character_array, widgets=[progressbar.Percentage(), "", progressbar.GranularBar()]):
            if character_piece[1] == 0:
                continue
            while True:
                try:
                    character_data = await get_character(session, character_piece[0])
                except:
                    print("\nError encountered! Retrying character....")
                    sleep(15)
                else:
                    break

            if "pictures" in character_data:
                pictures = []
                for value in character_data["pictures"]:
                    pictures.append(value["medium"])
                if type == "anime":
                    new_character = Character(
                        id=character_piece[0],
                        first_name=character_data["first_name"],
                        last_name=character_data["last_name"],
                        anime=series.title,
                        manga="",
                        game="",
                        images=pictures,
                        favorites=character_piece[1],
                    )
                    output_characters.append(new_character)
                if type == "manga":
                    new_character = Character(
                        id=character_piece[0],
                        first_name=character_data["first_name"],
                        last_name=character_data["last_name"],
                        anime="",
                        manga=series.title,
                        game="",
                        images=pictures,
                        favorites=character_piece[1],
                    )
                    output_characters.append(new_character)
        return output_characters


async def get_image_size(session: aiohttp.ClientSession, url) -> tuple | None:
    try:
        async with session.get(url=url) as response:
            resp = await response.read()
            image = io.BytesIO(resp)
            image_size = imagesize.get(image)
            return image_size
    except Exception as e:
        print("Unable to get url {} due to {}.".format(url, e.__class__))
        return None


async def write_to_file(session, characters: list[Character], bucket=None):
    series_dicts = [
        {"name": characters[0].anime, "type": "anime"},
        {"name": characters[0].manga, "type": "manga"},
        {"name": characters[0].game, "type": "game"},
    ]

    if bucket is not None:
        if bucket not in buckets_csv["name"].values:
            bucket_id = max(buckets_csv["id"]) + 1
            buckets_csv.loc[len(buckets_csv.index)] = [
                bucket_id, bucket]
        else:
            bucket_id = buckets_csv.loc[buckets_csv["name"]
                                        == bucket, "id"].values[0]
    else:
        bucket_id = 0

    for series in series_dicts:
        if series["name"] == "":
            continue
        series_name = series["name"]
        if series["name"] in series_csv["name"].values:
            return
        series_id = max(series_csv["id"]) + 1
        series_csv.loc[len(series_csv.index)] = [
            series_id, series["name"], series["type"], bucket_id]

        bucket_candidates = []
        for value in series_csv["name"].values:
            if series_name in value or value in series_name:
                if len(value) > 12:
                    bucket_candidates.append(value)

        if len(bucket_candidates) > 1 and len(series_name) > 12 and bucket == None:
            bucket = min(bucket_candidates, key=len)
            bucket_id = series_csv.loc[series_csv["name"]
                                       == bucket, "bucket"].values[0]
            if bucket_id == 0:
                if bucket not in buckets_csv["name"].values:
                    bucket_id = max(buckets_csv["id"]) + 1
                    buckets_csv.loc[len(buckets_csv.index)] = [
                        bucket_id, bucket]
                else:
                    bucket_id = buckets_csv.loc[buckets_csv["name"]
                                                == bucket, "id"].values[0]
            for s in bucket_candidates:
                series_csv.loc[series_csv["name"]
                               == s, "bucket"] = bucket_id

    for char in characters:
        if char.id in characters_csv["id"].values:
            series_correspondences_csv.loc[len(
                series_correspondences_csv.index)] = [char.id, series_id]
            continue

        for image in char.images:
            size = await get_image_size(session, image)
            if size and (size[0]/size[1] > 0.62 and size[0]/size[1] < 0.67):
                images_correspondences_csv.loc[len(
                    images_correspondences_csv.index)] = [char.id, image]
            else:
                char.images.remove(image)

        if len(char.images) > 0:
            characters_csv.loc[len(characters_csv.index)] = [
                char.id, char.first_name, char.last_name, char.get_value()]
            series_correspondences_csv.loc[len(
                series_correspondences_csv.index)] = [char.id, series_id]


async def add_series(session, series, index, type="anime", bucket=None):
    characters = await get_characters_in_series(
        session, series, type, index)
    await write_to_file(session, characters, bucket=bucket)


async def get_series():
    async with aiohttp.ClientSession() as session:
        series_ids = await get_series_from_ids(session, [30485], type="anime")
        # series_ids = await get_series_from_ids(session, [39681], type="anime")
        for i, series in enumerate(series_ids):
            await add_series(session, series, index=i+1, type="anime")

    characters_csv.to_csv("bot/data/characters.csv", sep="|", index=False)
    series_csv.to_csv("bot/data/series.csv", sep="|", index=False)
    series_correspondences_csv.to_csv(
        "bot/data/series_correspondences.csv", sep="|", index=False)
    images_correspondences_csv.to_csv(
        "bot/data/images_correspondences.csv", sep="|", index=False)
    buckets_csv.to_csv(
        "bot/data/buckets.csv", sep="|", index=False)


async def main():
    await get_series()

asyncio.run(main())
