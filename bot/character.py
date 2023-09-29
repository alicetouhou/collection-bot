from __future__ import annotations
import typing as t
import asyncpg


class Character:
    def __init__(
        self,
        images: list[str],
        id: int,
        first_name: str = "",
        last_name: str = "",
        series: list[dict[str, str]] = [],
        bucket: dict[str, str] | None = None,
        favorites: int = 0,
    ) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.series = series
        self.bucket = bucket
        self.images = images
        self.id = id
        self.value = favorites

    @classmethod
    def from_record(cls, data: dict[str, t.Any]) -> t.Self:
        return cls(
            [x["image"]
                for x in sorted(data["images"], key=lambda x: x['image_index'])
             ],
            data["id"],
            data["first_name"],
            data["last_name"],
            data["series"],
            data["bucket"],
            data["value"],
        )

    def __str__(self):
        return f"ID: {self.id}, First name: {self.first_name}, Last name: {self.last_name}, Anime: {self.anime}, Value: {self.value}, Images: {len(self.images)}"

    def get_images_str(self) -> str:
        return ",".join(self.images)

    def __eq__(self, other) -> bool:
        if isinstance(other, Character):
            return self.id == other.id
        return False
