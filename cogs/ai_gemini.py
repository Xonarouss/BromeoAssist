import os
import discord
from discord import app_commands
from discord.ext import commands
from google import genai

# ====== SYSTEM PROMPT ======
SYSTEM = (
    "Je bent BromeoASSIST in de Discord server 'Bromeo's LOUNGE'. "
    "Schrijf perfect Nederlands. Je bent vriendelijk, grappig, charmant en geïnteresseerd in leden. "
    "Houd antwoorden meestal compact en stel soms 1 korte vervolgvraag. "
    "Geen beledigingen of toxisch gedrag."
)

# ====== PROMPT BUILDER ======
def build_prompt(user_display_name: str, bericht: str) -> str:
    return f"{SYSTEM}\n\nGebruiker ({user_display_name}): {bericht}"

# ====== GEMINI HELPER ======
async def gemini_answer(client: genai.Client, user_display_name: str, bericht: str) -> str:
    model = "gemini-2.5-flash"
    prompt = build_prompt(user_display_name, bericht)

    resp = client.models.generate_content(
        model=model,
        contents=prompt
    )

    text = (resp.text or "").strip()
    if not text:
        text = "Oeps—ik kreeg even geen antwoord terug. Probeer het nog eens 🙂"

    return text[:1900]


# ====== DISCORD COG ======
class GeminiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY ontbreekt in .env")

        self.client = genai.Client(api_key=api_key)

    # /ai slash command
    @app_commands.command(
        name="ai",
        description="Praat met BromeoASSIST (Gemini AI)."
    )
    @app_commands.describe(bericht="Wat wil je zeggen?")
    async def ai(self, interaction: discord.Interaction, bericht: str):
        await interaction.response.defer(thinking=True)

        text = await gemini_answer(
            self.client,
            interaction.user.display_name,
            bericht
        )

        await interaction.followup.send(text)


# ====== SETUP ======
async def setup(bot: commands.Bot):
    cog = GeminiCog(bot)
    await bot.add_cog(cog)

    # Maak Gemini globaal beschikbaar voor andere cogs (ambient_ai)
    async def _bot_gemini_answer(user_display_name: str, bericht: str) -> str:
        return await gemini_answer(cog.client, user_display_name, bericht)

    bot.gemini_answer = _bot_gemini_answer
