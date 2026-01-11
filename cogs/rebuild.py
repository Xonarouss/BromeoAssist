import json
import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "server_config.json"

def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.guild and interaction.user and interaction.guild.owner_id == interaction.user.id

class RebuildCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rebuild_plan", description="Preview van de server rebuild (geen wijzigingen).")
    async def rebuild_plan(self, interaction: discord.Interaction):
        if not is_owner(interaction):
            return await interaction.response.send_message("Alleen de server owner kan dit gebruiken.", ephemeral=True)
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cats = cfg.get("categories", [])
        roles = cfg.get("roles", [])
        lines = [
            f"Server: **{cfg.get('server_name','(naam)')}**",
            f"Rollen: {', '.join([r['name'] for r in roles]) or '(geen)'}",
            "Categorieën/kanalen:"
        ]
        for c in cats:
            lines.append(f"- **{c['name']}**")
            for ch in c.get("channels", []):
                lines.append(f"  - {ch['type']}: {ch['name']}")
        await interaction.response.send_message("\n".join(lines)[:1900], ephemeral=True)

    @app_commands.command(name="rebuild_apply", description="Voer server rebuild uit volgens config (gevaarlijk).")
    @app_commands.describe(confirm="Typ exact: BROMEO REBUILD NU")
    async def rebuild_apply(self, interaction: discord.Interaction, confirm: str):
        if not is_owner(interaction):
            return await interaction.response.send_message("Alleen de server owner kan dit gebruiken.", ephemeral=True)
        if confirm.strip() != "BROMEO REBUILD NU":
            return await interaction.response.send_message("❌ Confirm mismatch. Typ exact: `BROMEO REBUILD NU`", ephemeral=True)

        await interaction.response.defer(thinking=True)
        guild: discord.Guild = interaction.guild  # type: ignore

        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

        # Server naam
        try:
            await guild.edit(name=cfg.get("server_name", guild.name))
        except discord.Forbidden:
            pass

        # Rollen maken (als ze nog niet bestaan)
        existing_roles = {r.name: r for r in guild.roles}
        for r in cfg.get("roles", []):
            if r["name"] in existing_roles:
                continue
            try:
                color = discord.Color.from_str(r.get("color", "#99aab5"))
                await guild.create_role(
                    name=r["name"],
                    colour=color,
                    hoist=bool(r.get("hoist", False)),
                    reason="BromeoASSIST rebuild"
                )
            except discord.Forbidden:
                pass

        # Categorieën + kanalen
        existing_cats = {c.name: c for c in guild.categories}
        for c in cfg.get("categories", []):
            cat = existing_cats.get(c["name"])
            if not cat:
                try:
                    cat = await guild.create_category(c["name"], reason="BromeoASSIST rebuild")
                except discord.Forbidden:
                    continue

            existing_channels = {ch.name: ch for ch in cat.channels}
            for ch in c.get("channels", []):
                if ch["name"] in existing_channels:
                    continue
                try:
                    if ch["type"] == "text":
                        await guild.create_text_channel(ch["name"], category=cat, reason="BromeoASSIST rebuild")
                    elif ch["type"] == "voice":
                        await guild.create_voice_channel(ch["name"], category=cat, reason="BromeoASSIST rebuild")
                except discord.Forbidden:
                    continue

        await interaction.followup.send("✅ Rebuild uitgevoerd (zonder wipe). Pas `server_config.json` aan voor jouw ideale indeling.")

async def setup(bot):
    await bot.add_cog(RebuildCog(bot))
