import math

class Character:
    first_name = ""
    last_name = ""
    anime = ""
    images = []
    favorites = 0
    value = 0

    def __init__(self, first_name=first_name, last_name=last_name, anime=anime, images=images, id=id, favorites=favorites):
        self.first_name = first_name
        self.last_name = last_name
        self.anime = anime
        self.images = images
        self.id = id
        self.favorites = favorites
        self.value = self.get_value()

    def __init__(self, data: tuple):
        self.first_name = data[1]
        self.last_name = data[2]
        self.anime = data[3].split(",")
        self.images = data[4].split(",")
        self.id = data[0]
        self.value = data[5]

    def __str__(self):
        return f'ID: {self.id}, First name: {self.first_name}, Last name: {self.last_name}, Anime: {self.anime}, Value: {self.value}, Images: {len(self.images)}'
    
    def get_value(self) -> int:
        if int(self.favorites) > 0:
            return max(math.floor(200 * math.log(int(self.favorites), 10) - 100),15)
        return 10
    
    def get_images_str(self) -> str:
        return ",".join(self.images)