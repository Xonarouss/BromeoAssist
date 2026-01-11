import os
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

BASE = "https://fortnite-api.com/v2"

class FortniteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("FORTNITE_API_KEY")
        if not self.api_key:
            raise RuntimeError("FORTNITE_API_KEY ontbreekt in .env")

    async def _get(self, url: str, params: dict | None = None):
        headers = {"Authorization": self.api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as r:
                data = await r.json(content_type=None)
                return r.status, data

    @app_commands.command(name="fortnite", description="Fortnite: player stats (BR).")
    @app_commands.describe(naam="Epic display name")
    async def fortnite(self, interaction: discord.Interaction, naam: str):
        await interaction.response.defer(thinking=True)
        status, data = await self._get(f"{BASE}/stats/br/v2", {"name": naam})
        if status != 200 or not data.get("data"):
            return await interaction.followup.send(f"❌ Geen stats gevonden voor **{naam}**.")

        overall = data["data"]["stats"]["all"]["overall"]
        msg = (
            f"🎮 **Fortnite stats — {naam}**\n"
            f"• Wins: **{overall.get('wins')}**\n"
            f"• Kills: **{overall.get('kills')}**\n"
            f"• Matches: **{overall.get('matches')}**\n"
            f"• K/D: **{overall.get('kd')}**\n"
        )
        await interaction.followup.send(msg)

    @app_commands.command(name="fn_shop", description="Fortnite: huidige item shop.")
    async def shop(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        status, data = await self._get(f"{BASE}/shop/br")
        if status != 200 or not data.get("data"):
            return await interaction.followup.send("❌ Kon shop niet ophalen.")
        # Compact overzicht
        entries = data["data"].get("featured", {}).get("entries", [])[:5]
        lines = []
        for e in entries:
            items = e.get("items", [])
            if items:
                lines.append(f"- {items[0].get('name','(unknown)')}")
        txt = "🛒 **Featured shop (top 5)**\n" + ("\n".join(lines) if lines else "(geen data)")
        await interaction.followup.send(txt)

    @app_commands.command(name="fn_news", description="Fortnite: BR nieuws.")
    async def news(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        status, data = await self._get(f"{BASE}/news/br")
        if status != 200 or not data.get("data"):
            return await interaction.followup.send("❌ Kon nieuws niet ophalen.")
        motds = data["data"].get("motds", [])[:3]
        lines = [f"- **{m.get('title','')}**: {m.get('body','')[:140]}..." for m in motds]
        await interaction.followup.send("📰 **Fortnite BR nieuws**\n" + ("\n".join(lines) if lines else "(geen items)"))

async def setup(bot):
    await bot.add_cog(FortniteCog(bot))
