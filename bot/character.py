from __future__ import annotations

import typing as t
import copy

import asyncpg

import hikari
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

    async def _get_embed(self, image) -> hikari.Embed:
        name = f"{self.first_name} {self.last_name} • {self.value}<:wishfragments:1148459769980530740>"

        anime_list = sorted(self.anime)
        manga_list = sorted(self.manga)
        games_list = sorted(self.games)
        series_list = []
        count = 0
        for manga in manga_list:
            if manga != "":
                series_list.append(f"📖 {manga}")
        for anime in anime_list:
            if anime != "":
                series_list.append(f"🎬 {anime}")
        for game in games_list:
            if game != "":
                series_list.append(f"🎮 {game}")

        extra_length = len(self.get_series()) - 4

        if extra_length > 0:
            series_list = series_list[:4]
            series_list.append(f"*and {extra_length} more..*")

        embed = hikari.Embed(title=name, color="f598df",
                             description="\n".join(series_list))
        embed.set_image(image)

        return embed

    async def get_navigator(self) -> nav.NavigatorView:
        pages = []
        embed = await self._get_embed(self.images[0])

        for image in self.images:
            new_embed = copy.deepcopy(embed)
            new_embed.set_image(image)
            pages.append(new_embed)

        buttons = [nav.PrevButton(), nav.IndicatorButton(), nav.NextButton()]
        navigator = nav.NavigatorView(pages=pages, buttons=buttons)
        return navigator

    async def get_claimable_embed(self) -> hikari.Embed:
        embed = await self._get_embed(self.images[0])
        return embed

    def __eq__(self, other) -> bool:
        if isinstance(other, Character):
            return self.id == other.id
        return False
