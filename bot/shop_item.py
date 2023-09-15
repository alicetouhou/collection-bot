import crescent
from typing import TYPE_CHECKING
from bot.upgrades import Upgrades, UpgradeEffects

if TYPE_CHECKING:
    from bot.user import User


class ShopItem:
    def __init__(self, name: str, description: str | None, price: int, icon, proper_name: bool = True) -> None:
        self.name: str = name
        self.description: str | None = description
        self.price: int = price
        self.icon: str = icon
        self.proper_name: bool = proper_name
        self.lowercase_name = name.lower()

    def cased_name(self) -> str:
        return self.name if self.proper_name == True else self.lowercase_name

    def article(self) -> str:
        return "The" if self.proper_name == True else "a"

    def description_line(self) -> str:
        return f"**{self.icon} Buy a {self.cased_name()}: {self.price}<:wishfragments:1148459769980530740>**\n*{self.description}*"

    async def purchased(self, ctx: crescent.Context, user: 'User') -> bool:
        await ctx.respond(
            f"You purchased {self.article()} **{self.cased_name()}**!\n<:wishfragments:1148459769980530740> Wish fragments remaining: **{(await user.currency) - self.price}**"
        )
        return False


class Upgrade(ShopItem):
    def __init__(self, name: str, description: str | None, price: int, icon, level: int, multiplier: float, type: Upgrades, proper_name: bool = True) -> None:
        price = int(pow(multiplier, level) * price)
        self.level = level
        self.type = type
        super().__init__(name, description, price, icon, proper_name)

    def description_line(self) -> str:
        desc = f"**{self.icon} {self.cased_name()} • `Lv{self.level} → Lv{self.level+1}` • {self.price}<:wishfragments:1148459769980530740>**\n*{self.description}*"
        return self.formatted_description(desc)

    def formatted_description(self, description) -> str:
        upgrade_type = UpgradeEffects.upgrades[self.type]
        description = description.replace(
            "$1", upgrade_type.formatted_modifier(self.level))
        description = description.replace(
            "$2", upgrade_type.formatted_modifier(self.level+1))
        return description

    async def purchased(self, ctx: crescent.Context, user: 'User') -> bool:
        await user.increase_upgrade_level(self.type)
        await super().purchased(ctx, user)
        return True


class Roll(ShopItem):
    def __init__(self) -> None:
        super().__init__(
            name="Roll",
            description="A roll allows you to roll one more time on the roulette.",
            price=250,
            icon="🎲",
            proper_name=False
        )

    async def purchased(self, ctx: crescent.Context, user: 'User') -> bool:
        rolls = await user.rolls
        await user.set_rolls(rolls + 1)
        await super().purchased(ctx, user)
        return True


class Claim(ShopItem):
    def __init__(self) -> None:
        super().__init__(
            name="Claim",
            description="A claim allows you to claim one more character from the roulette.",
            price=600,
            icon="🥅",
            proper_name=False
        )

    async def purchased(self, ctx: crescent.Context, user: 'User') -> bool:
        claims = await user.claims
        await user.set_rolls(claims + 1)
        await super().purchased(ctx, user)
        return True


class ForbiddenScroll(ShopItem):
    def __init__(self) -> None:
        super().__init__(
            name="Forbidden Scroll",
            description="After purchasing, you can use this item to claim any character by ID.",
            price=5000,
            icon="📜",
            proper_name=True
        )

    async def purchased(self, ctx: crescent.Context, user: 'User') -> bool:
        claims = await user.claims
        await user.set_rolls(claims + 1)
        await super().purchased(ctx, user)
        return True


class RollGenerationRate(Upgrade):
    def __init__(self, level: int) -> None:
        super().__init__(
            level=level,
            name="Roll Generation",
            description="Reduce your roll generation speed from **$1** to **$2**.",
            price=800,
            multiplier=1.4,
            icon="🎲",
            proper_name=True,
            type=Upgrades.ROLL_REGEN
        )


class RollMaximum(Upgrade):
    def __init__(self, level: int) -> None:
        super().__init__(
            level=level,
            name="Maximum Rolls",
            description="Increase the number of rolls that can be generated before generation stops from **$1** to **$2**.",
            price=800,
            multiplier=1.4,
            icon="🎲",
            proper_name=True,
            type=Upgrades.ROLL_MAX
        )


class WishlistSize(Upgrade):
    def __init__(self, level: int) -> None:
        super().__init__(
            level=level,
            name="Wishlist Size",
            description="Increase the maximum size of your wishlist from **$1** to **$2**.",
            price=800,
            multiplier=1.4,
            icon="🌟",
            proper_name=True,
            type=Upgrades.WISHLIST_SIZE
        )


class WishlistRateUp(Upgrade):
    def __init__(self, level: int) -> None:
        super().__init__(
            level=level,
            name="Wishlist Rate",
            description="Increase the chance of rolling a wishlisted character from **$1** to **$2**.",
            price=800,
            multiplier=1.4,
            icon="🌟",
            proper_name=True,
            type=Upgrades.WISHLIST_RATE_BONUS
        )


class FragmentBonus(Upgrade):
    def __init__(self, level: int) -> None:
        super().__init__(
            level=level,
            name="Fragment Multiplier",
            description="When you get new fragments from the roulette, increase the multiplcation amount from **$1** to **$2**.",
            price=600,
            multiplier=1.445,
            icon="<:wishfragments:1148459769980530740>",
            proper_name=True,
            type=Upgrades.FRAGMENT_BONUS
        )


class DailyBounty(Upgrade):
    def __init__(self, level: int) -> None:
        super().__init__(
            level=level,
            name="Daily Bounty",
            description="Increase the number of claims you get daily from **$1** to **$2**, and increase the number of wish fragments you get.",
            price=1200,
            multiplier=1.69,
            icon="🥅",
            proper_name=True,
            type=Upgrades.DAILY_BONUS
        )


shop_items = (
    Roll(),
    Claim(),
    # ForbiddenScroll(),
)
