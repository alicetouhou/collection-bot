import random

import crescent
import hikari

from bot.model import Plugin

plugin = Plugin()

total_rates = {
    3: 200,
    4: 60,
    5: 20,
    6: 18,
    7: 12,
    8: 8,
    9: 6,
    10: 6,
    11: 6,
    12: 6,
    13: 8,
    14: 12,
    15: 18,
    16: 20,
    17: 60,
    18: 200,
}

die_faces = {
    1: "<:face_1:1161368125611200693>",
    2: "<:face_2:1161368127477657720>",
    3: "<:face_3:1161368128475906068>",
    4: "<:face_4:1161368129746784286>",
    5: "<:face_5:1161368131101536397>",
    6: "<:face_6:1161368124273201232>",
}

sicbo_group = crescent.Group("sicbo")


async def betting_type_autocomplete(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return [
        ("big", "big"),
        ("small", "small"),
        ("double (requires number)", "double"),
        ("triple (requires number)", "triple"),
        ("total (requires number)", "total"),
    ]


@plugin.include
@sicbo_group.child
@crescent.command(
    name="play",
    description="Play a round of sic bo.",
)
class InfoCommand:
    wager = crescent.option(
        int,
        "Wager an amount. The payout is dependent on your betting type.",
        name="wager",
    )
    betting_type = crescent.option(
        str,
        "Choose a type to bet.",
        name="bettingtype",
        autocomplete=betting_type_autocomplete
    )
    parameter = crescent.option(
        int,
        "Choose a number, if your bet requires it.",
        name="bettingnumber",
        default=None
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        user = await plugin.model.dbsearch.create_user(ctx.guild_id, ctx.user)

        if self.wager > user.currency:
            await ctx.respond(
                "You do not have enough <:wishfragments:1148459769980530740> wish fragments to make that wager. Try gambling more! Maybe you can reach the number you want faster 🙂"
            )
            return

        diceroll_1 = random.randint(1, 6)
        diceroll_2 = random.randint(1, 6)
        diceroll_3 = random.randint(1, 6)
        sum = diceroll_1 + diceroll_2 + diceroll_3
        result = ""

        match self.betting_type:
            case "big":
                if not (diceroll_1 == diceroll_2 and diceroll_2 == diceroll_3 and diceroll_1):
                    if sum >= 11:
                        await user.set_currency(user.currency + self.wager)
                        result = f"Congrats! I rolled a number 11 or greater, and your wager doubled from **<:wishfragments:1148459769980530740>{self.wager}** to **<:wishfragments:1148459769980530740>{self.wager * 2}**. You now have <:wishfragments:1148459769980530740>**{user.currency}** wish fragments"
            case "small":
                if not (diceroll_1 == diceroll_2 and diceroll_2 == diceroll_3 and diceroll_1):
                    if sum <= 10:
                        await user.set_currency(user.currency + self.wager)
                        result = f"Congrats! I rolled a number 10 or lower, and your wager doubled from **<:wishfragments:1148459769980530740>{self.wager}** to **<:wishfragments:1148459769980530740>{self.wager * 2}**. You now have <:wishfragments:1148459769980530740>**{user.currency}** wish fragments"
            case "double":
                if ((diceroll_1 == diceroll_2 or diceroll_1 == diceroll_3) and diceroll_1 == self.parameter) \
                        or (diceroll_2 == diceroll_3 and diceroll_2 == self.parameter):
                    await user.set_currency(user.currency + self.wager * 9)
                    result = f"Congrats! I rolled **{self.parameter}** at least 2 times, and your wager dectupled from **<:wishfragments:1148459769980530740>{self.wager}** to **<:wishfragments:1148459769980530740>{self.wager * 10}**. You now have <:wishfragments:1148459769980530740>**{user.currency}** wish fragments"
            case "triple":
                if diceroll_1 == diceroll_2 and diceroll_2 == diceroll_3 and diceroll_1 == self.parameter:
                    await user.set_currency(user.currency + self.wager * 199)
                    result = f"Congrats! I rolled **{self.parameter}** 3 times, and your wager increased 200x from **<:wishfragments:1148459769980530740>{self.wager}** to **<:wishfragments:1148459769980530740>{self.wager * 200}**. You now have <:wishfragments:1148459769980530740>**{user.currency}** wish fragments"
            case "total":
                if sum == self.parameter:
                    payout_amount = total_rates[self.parameter]
                    await user.set_currency(user.currency + self.wager * (payout_amount - 1))
                    result = f"Congrats! The sum of the three dice I rolled is **{self.parameter}**, and your wager increased {payout_amount}x from **<:wishfragments:1148459769980530740>{self.wager}** to **<:wishfragments:1148459769980530740>{self.wager * payout_amount}**. You now have <:wishfragments:1148459769980530740>**{user.currency}** wish fragments"
            case _:
                await ctx.respond("Your betting type was not valid.")
                return

        if result == "":
            await user.set_currency(user.currency - self.wager)
            result = f"Too bad! You lost your bet and lost your wager of {self.wager}. You now have <:wishfragments:1148459769980530740>**{user.currency}** wish fragments"

        die_images = f"**{die_faces[diceroll_1]} {die_faces[diceroll_2]} {die_faces[diceroll_3]} {sum}**"

        embed = hikari.embeds.Embed(
            title=f"Sic bo results · `{self.betting_type}`", color="f598df", description=f"{die_images}\n\n{result}")

        await ctx.respond(embed)


@plugin.include
@sicbo_group.child
@crescent.command(
    name="rules",
    description="List the rules of sic bo.",
)
async def sicbo_help(ctx: crescent.Context):

    description = "Sic bo is a dice game originating from China. Three dice are rolled, and the goal is to bet on the outcome of the three dice. If you are correct, your wager increases by the payout amount. Otherwise, you lose your wager."

    embed = hikari.embeds.Embed(
        title=f"What is sic bo?", color="f598df", description=description)

    betting_options = "`big` - The number rolled is 11 or greater (excluding triples). **1 to 1** payout.\n" \
                      "`small` - The number rolled is 10 or less (excluding triples). **1 to 1** payout.\n" \
                      "`double` - The number you choose (1-6) is rolled at least twice. **10 to 1** payout.\n" \
                      "`triple` - The number you choose (1-6) is rolled three times. **180 to 1** payout.\n" \
                      "`total`- The number you choose (4-17) is the sum of the three dice. Payout varies based on the number you choose.\n" \
                      "*4 or 17*: 1 to 60, *5 or 16*: 1 to 20, *6 or 15*: 1 to 18, *7 or 14*: 1 to 12, *8 or 13*: 1 to 8, *9 to 12*: 1 to 6"

    embed.add_field(name="Betting options:",
                    value=betting_options)

    await ctx.respond(embed)
