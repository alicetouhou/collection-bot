import hikari
import psycopg2

class Model:
    def __init__(self) -> None:
        ...

    async def on_start(self, _: hikari.StartedEvent) -> None:
        ...

    async def on_stop(self, _: hikari.StoppedEvent) -> None:
        """
        This function is called when your bot stops. This is a good place to put
        cleanup functions for the model class.
        """
        ...
