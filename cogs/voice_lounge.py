import asyncio
import discord
from discord.ext import commands

VOICE_CHANNEL_NAME = "Praat met BromeoASSIST"

# Optioneel: zet dit op de naam van jouw category waar voice kanalen onder staan.
# Laat None als het je niet uitmaakt.
PREFERRED_CATEGORY_NAMES = [
    "Video/Voice Channels",
    "Video/Voice",
    "Voice Channels",
    "Voice",
]


class VoiceLounge(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._task = self.bot.loop.create_task(self._keep_alive_loop())

    def cog_unload(self):
        try:
            self._task.cancel()
        except Exception:
            pass

    def _find_preferred_category(self, guild: discord.Guild) -> discord.CategoryChannel | None:
        cats = guild.categories or []
        for pref in PREFERRED_CATEGORY_NAMES:
            for c in cats:
                if c.name.strip().lower() == pref.strip().lower():
                    return c
        return None

    async def _ensure_voice_channel(self, guild: discord.Guild) -> discord.VoiceChannel | None:
        # 1) Bestaat al?
        for ch in guild.voice_channels:
            if ch.name == VOICE_CHANNEL_NAME:
                return ch

        # 2) Probeer aan te maken
        try:
            category = self._find_preferred_category(guild)
            ch = await guild.create_voice_channel(
                name=VOICE_CHANNEL_NAME,
                category=category
            )
            return ch
        except Exception:
            return None

    async def _ensure_connected(self, guild: discord.Guild):
        target = await self._ensure_voice_channel(guild)
        if not target:
            return

        vc = guild.voice_client
        if vc and vc.is_connected():
            if vc.channel and vc.channel.id == target.id:
                return
            try:
                await vc.move_to(target)
            except Exception:
                pass
            return

        try:
            await target.connect()
        except Exception:
            pass

    async def _keep_alive_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                for guild in self.bot.guilds:
                    await self._ensure_connected(guild)
            except Exception:
                pass
            await asyncio.sleep(30)


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceLounge(bot))
