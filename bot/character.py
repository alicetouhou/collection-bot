from __future__ import annotations

import math
import typing as t

import asyncpg

import hikari
import miru
from miru.ext import nav


class Character:
    def __init__(
        self,
        images: list[str],
        games: list[str],
        id: int,
        first_name: str = "",
        last_name: str = "",
        anime: list[str] = [],
        favorites: int = 0,
        manga: list[str] = [],
    ) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.anime = anime
        self.manga = manga
        self.games = games
        self.images = images
        self.id = id
        self.value = favorites

    @classmethod
    def from_record(cls, data: asyncpg.Record) -> t.Self:
        return cls(
            data[4].split(","),
            data[7].split(","),
            data[0],
            data[1],
            data[2],
            data[3].split(","),
            data[5],
            data[6].split(","),
        )

    def __str__(self):
        return f"ID: {self.id}, First name: {self.first_name}, Last name: {self.last_name}, Anime: {self.anime}, Value: {self.value}, Images: {len(self.images)}"

    def get_images_str(self) -> str:
        return ",".join(self.images)

    def get_series(self) -> list[str]:
        series = sorted(self.anime + self.manga + self.games)
        filtered_series = filter(lambda x: x != '', series)
        return list(filtered_series)

    def _get_embed(self, image) -> hikari.Embed:
        name = self.first_name + " " + self.last_name
        description = f"ID `{self.id}` • {self.value}<:wishfragments:1148459769980530740>"

        anime_list = sorted(self.anime)
        manga_list = sorted(self.manga)
        games_list = sorted(self.games)
        animeography = ""
        count = 0
        for manga in manga_list:
            animeography += f"📖 {manga}\n" if manga != "" and count <= 4 else ""
            count += 1
        for anime in anime_list:
            animeography += f"🎬 {anime}\n" if anime != "" and count <= 4 else ""
            count += 1
        for game in games_list:
            animeography += f"🎮 {game}\n" if game != "" and count <= 4 else ""
            count += 1
        if count >= 4:
            animeography += f"*and {count-4} more..*"

        embed = hikari.Embed(title=name, color="f598df",
                             description=description)
        embed.set_image(image)
        embed.add_field(name="Appears in:", value=animeography)

        return embed

    def get_navigator(self) -> nav.NavigatorView:
        pages = []

        for image in self.images:
            embed = self._get_embed(image)
            pages.append(embed)

        buttons = [nav.PrevButton(), nav.IndicatorButton(), nav.NextButton()]
        navigator = nav.NavigatorView(pages=pages, buttons=buttons)
        return navigator

    def get_claimable_embed(self) -> hikari.Embed:
        embed = self._get_embed(self.images[0])
        return embed
