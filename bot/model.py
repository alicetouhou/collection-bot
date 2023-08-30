import hikari


class Model:
    def __init__(self) -> None:
        ...

    async def on_start(self, _: hikari.StartedEvent) -> None:
        """
        This function is called when your bot starts. This is a good place to open a
        connection to a database, aiohttp client, or similar.
        """
        ...

    async def on_stop(self, _: hikari.StoppedEvent) -> None:
        """
        This function is called when your bot stops. This is a good place to put
        cleanup functions for the model class.
        """
        ...
