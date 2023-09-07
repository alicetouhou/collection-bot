from __future__ import annotations

import math
import typing as t

import asyncpg


class Character:
    def __init__(
        self,
        images: list[str],
        games: list[str],
        id: int,
        first_name: str = "",
        last_name: str = "",
        anime: str = "",
        favorites: int = 0,
        manga: str = "",
    ) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.anime = anime
        self.manga = manga
        self.games = games
        self.images = images
        self.id = id
        self.favorites = favorites
        self.value = self.get_value()

    @classmethod
    def from_record(cls, data: asyncpg.Record) -> t.Self:
        return cls(
            data[1],
            data[2],
            data[3].split(","),
            data[4].split(","),
            data[0],
            data[5],
            data[6].split(","),
            data[7].split(","),
        )

    def __str__(self):
        return f"ID: {self.id}, First name: {self.first_name}, Last name: {self.last_name}, Anime: {self.anime}, Value: {self.value}, Images: {len(self.images)}"

    def get_value(self) -> int:
        if int(self.favorites) > 0:
            return max(math.floor(200 * math.log(int(self.favorites), 10) - 100), 15)
        return 10

    def get_images_str(self) -> str:
        return ",".join(self.images)
