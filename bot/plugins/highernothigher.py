import random

import crescent
import hikari
import miru
import typing as t

from bot.model import Plugin

plugin = Plugin()

highernothigher_group = crescent.Group("highernothigher")


def create_board(height, width) -> list[list[int]]:
    board = [[(i + k) % 10 + 1 for i in range(1, height + 1)]
             for k in range(width)]
    random.shuffle(board)
    board = [[board[x][y] for x in range(width)] for y in range(height)]
    random.shuffle(board)
    return board


def generate_grid() -> list[list[dict[str, int]]]:
    width = 4
    height = 4

    values = create_board(height, width)

    grid: list[list[dict[str, int]]] = []

    for i, row in enumerate(values):
        grid.append([])
        for j, value in enumerate(row):
            highest_number_row = row.index(max(row))
            column_array = [values[row][j] for row in range(0, height)]
            highest_number_column = column_array.index(
                max(column_array))

            direction = 0
            if row[highest_number_row] == value and column_array[highest_number_column] == value:
                direction = 0
            elif row[highest_number_row] > column_array[highest_number_column]:
                if highest_number_row > j:
                    direction = 2
                else:
                    direction = 4
            else:
                if highest_number_column > i:
                    direction = 3
                else:
                    direction = 1

            grid[i].append({"value": value, "direction": direction})

    return grid


class BoardView(miru.View):
    grid: list[list[dict[str, int]]]

    directions = {
        0: "🔄",
        1: "⬆️",
        2: "➡️",
        3: "⬇️",
        4: "⬅️"
    }

    def __init__(self, *, timeout: float, grid: list[list[dict[str, int]]], embed: hikari.Embed, goal: int, wager: int, original_user: hikari.User) -> None:
        super().__init__(timeout=timeout)
        self.grid = grid
        self.embed = embed
        self.sum = 0
        self.goal = goal
        self.wager = wager
        self.original_user = original_user

    def get_payout(self) -> int:
        return int(self.wager * pow((self.sum * 1.358 / self.goal), 3))

    def reveal_button(self, button: miru.Button | t.Any, cell: int):
        button.disabled = True
        button.style = hikari.ButtonStyle.SECONDARY
        c = self.grid[int(cell / 4)][cell % 4]
        self.sum += c['value']
        button.label = str(c['value'])
        button.emoji = hikari.UnicodeEmoji(self.directions[c['direction']])

    async def _button_scripts(self, button: miru.Button, ctx: miru.ViewContext, cell: int) -> None:
        if self.message is None:
            return

        if ctx.user != self.original_user:
            return

        self.reveal_button(button, cell)

        payout = self.get_payout()
        self.embed = self.embed.edit_field(
            0, "Total sum", f"{self.sum} / {self.goal}")

        if self.sum > self.goal:
            self.stop()
            await self.on_timeout()
            self.embed = self.embed.edit_field(
                1, "Payout", f"<:wishfragments:1148459769980530740>0")
            await self.message.edit(embed=self.embed, components=self)
            if ctx.guild_id is None:
                return
            user = await plugin.model.dbsearch.create_user(ctx.guild_id, ctx.user)
            await ctx.respond(f"Whoops! Your sum is higher than the goal. Your wager was lost. You now have <:wishfragments:1148459769980530740>**{user.currency}** wish fragments.")
            return

        self.embed = self.embed.edit_field(
            1, "Payout", f"<:wishfragments:1148459769980530740>{payout}")
        await self.message.edit(embed=self.embed, components=self)

    # Row 0
    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=0)
    async def button_zero(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 0)

    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=0)
    async def button_one(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 1)

    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=0)
    async def button_two(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 2)

    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=0)
    async def button_three(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 3)

    # Row 1
    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_four(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 4)

    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_five(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 5)

    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_six(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 6)

    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_seven(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 7)

    # Row 2
    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=2)
    async def button_eight(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 8)

    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=2)
    async def button_nine(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 9)

    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=2)
    async def button_ten(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 10)

    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=2)
    async def button_eleven(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 11)

    # Row 3
    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=3)
    async def button_twelve(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 12)

    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=3)
    async def button_thirteen(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 13)

    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=3)
    async def button_fourteen(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 14)

    @miru.button(label="", emoji="❔", style=hikari.ButtonStyle.SECONDARY, row=3)
    async def button_fifteen(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self._button_scripts(button, ctx, 15)

    @miru.button(label="Submit!", emoji="✅", style=hikari.ButtonStyle.PRIMARY, row=4)
    async def button_lock_in(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        if ctx.user != self.original_user:
            return
        if ctx.guild_id is None:
            return
        self.stop()
        user = await plugin.model.dbsearch.create_user(ctx.guild_id, ctx.user)
        payout = self.get_payout()
        await user.set_currency(user.currency + payout)
        await ctx.respond(
            f"Congrats! I flipped heads, and your wager increased from **<:wishfragments:1148459769980530740>{self.wager}** to **<:wishfragments:1148459769980530740>{payout}**. You now have <:wishfragments:1148459769980530740>**{user.currency}** wish fragments."
        )
        await self.on_timeout()

    async def on_timeout(self) -> None:
        for index, item in enumerate(self.children):
            if index <= 15:
                self.reveal_button(item, index)
            else:
                item.disabled = True
        if self.message is None:
            return
        await self.message.edit(components=self)


@plugin.include
@highernothigher_group.child
@crescent.command(
    name="play",
    description="Play a round of \"Higher, not Higher\".",
)
class GameCommand:
    wager = crescent.option(
        int,
        "Wager an amount. The payout is dependent on your betting type.",
        name="wager",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        user = await plugin.model.dbsearch.create_user(ctx.guild_id, ctx.user)

        if self.wager > user.currency:
            await ctx.respond(
                "You do not have enough <:wishfragments:1148459769980530740> wish fragments to make that wager. Try gambling more! Maybe you can reach the number you want faster 🙂"
            )
            return
        grid = generate_grid()

        goal = random.randint(25, 45)

        description = f"Your target value is **{goal}**. Try to reach the target value without going over! " \
            "The closer you get, the more <:wishfragments:1148459769980530740> wish fragments you get back, but if you go over you lose your wager. " \
            "\nClick on a box to reveal it and increase your sum by it's value. " \
            "After revealing a box, both it's sum and arrow are revealed. The arrow points to the highest value box that's in the same row or column as the revealed box."

        embed = hikari.embeds.Embed(
            title=f"Higher, not Higher!", color="f598df", description=description)
        embed.add_field(name="Total sum", value=f"0 / {goal}", inline=True)
        embed.add_field(
            name="Payout", value=f"<:wishfragments:1148459769980530740>0", inline=True)

        view: miru.View = BoardView(
            timeout=300, grid=grid, embed=embed, goal=goal, wager=self.wager, original_user=ctx.user)

        message = await ctx.respond(
            "",
            embed=embed,
            components=view,
            ensure_message=True,
        )

        await view.start(message)
        await user.set_currency(user.currency - self.wager)


@plugin.include
@highernothigher_group.child
@crescent.command(
    name="rules",
    description="List the rules of higher not higher.",
)
async def sicbo_help(ctx: crescent.Context):

    description = f"Your target value is a number between 25 and 45. Try to reach the target value without going over! " \
        "The closer you get, the more <:wishfragments:1148459769980530740> wish fragments you get back, but if you go over you lose your wager. " \
        "\nClick on a box to reveal it and increase your sum by it's value. " \
        "After revealing a box, both it's sum and arrow are revealed. The arrow points to the highest value box that's in the same row or column as the revealed box."

    embed = hikari.embeds.Embed(
        title=f"What is higher not higher?", color="f598df", description=description)

    await ctx.respond(embed)
