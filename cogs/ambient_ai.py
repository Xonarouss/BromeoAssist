import time
import random
import discord
from discord.ext import commands

# ====== TUNING ======
DEFAULT_REPLY_CHANCE = 0.25   # 25% in normale allowed kanalen
NSFW_REPLY_CHANCE = 0.50      # 50% in 💬│ᴅᴇ-ʟᴏᴜɴɢᴇ-🔞

USER_COOLDOWN_SEC = 10
CHANNEL_COOLDOWN_SEC = 5
MIN_MESSAGE_CHARS = 12
MAX_REPLIES_PER_CHANNEL_PER_5MIN = 3

# Extra: als Gemini quota op is (429), zet ambient even op pauze
QUOTA_BACKOFF_SEC = 60


# ====== CHANNELS (EXACTE NAMEN) ======
# Let op: kopieer exact zoals Discord het toont (emoji + │ + speciale letters)
ALLOWED_CHANNEL_NAMES = {
    "💬│ᴅᴇ-ʟᴏᴜɴɢᴇ",
    "💬│ᴅᴇ-ʟᴏᴜɴɢᴇ-🔞",
    "🐸│ᴍᴇᴍᴇs",
    "👥│ᴠɪɴᴅ-ɢᴀᴍᴇ-ᴍᴀᴀᴛᴊᴇ",
    "🎂│ᴠᴇʀᴊᴀᴀʀᴅᴀɢᴇɴ",
    "🐱│ʜᴜɪsᴅɪᴇʀᴇɴ",
    "🏆│ʜᴀʟʟ-ᴏꜰ-ꜰᴀᴍᴇ",
}

# Kanalen waar hij NOOIT “ambient” moet praten (mentions/replies werken nog wel)
BLOCKED_CHANNEL_NAMES = {
    "📣│ᴀᴀɴᴋᴏɴᴅɪɢɪɴɢᴇɴ",
    "📌│ʜᴜɪsʀᴇɢᴇʟs",
    "📚│ᴅɪsᴄᴏʀᴅ-ᴛᴜᴛᴏʀɪᴀʟ",
    "📱│sᴏᴄɪᴀʟs",
    "🎁│ɪᴛᴇᴍ-sʜᴏᴘ",
    "🛡️│ᴍᴏᴅᴇʀᴀᴛᴏʀ-ᴄʜᴀᴛ",
    "🧰│ᴍᴏᴅs-ᴇɴ-ᴛᴇᴄʜ-ᴄʜᴀᴛ",
    "🧾│sᴇʀᴠᴇʀʟᴏɢ",
    "📢│sᴇʀᴠᴇʀ-ʙᴇʀɪᴄʜᴛᴇɴ",
    "🎟️│ᴛɪᴄᴋᴇᴛs",
    "🧑‍💻│sᴜᴘᴘᴏʀᴛ",
}

# Speciaal kanaal met 50% kans
NSFW_CHANNEL_NAME = "💬│ᴅᴇ-ʟᴏᴜɴɢᴇ-🔞"


class AmbientAI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_user = {}
        self._last_channel = {}
        self._channel_burst = {}  # channel_id -> list[timestamps]
        self._quota_block_until = 0.0

    def _now(self) -> float:
        return time.time()

    def _is_text_channel(self, ch) -> bool:
        return isinstance(ch, (discord.TextChannel, discord.Thread))

    def _channel_name(self, message: discord.Message) -> str:
        return getattr(message.channel, "name", "") or ""

    def _is_blocked(self, message: discord.Message) -> bool:
        name = self._channel_name(message)
        return name.lower() in {n.lower() for n in BLOCKED_CHANNEL_NAMES}

    def _is_allowed(self, message: discord.Message) -> bool:
        name = self._channel_name(message)
        return name.lower() in {n.lower() for n in ALLOWED_CHANNEL_NAMES}

    def _cooldown_ok(self, message: discord.Message) -> bool:
        t = self._now()
        uid = message.author.id
        cid = message.channel.id

        # quota backoff
        if t < self._quota_block_until:
            return False

        if t - self._last_user.get(uid, 0) < USER_COOLDOWN_SEC:
            return False
        if t - self._last_channel.get(cid, 0) < CHANNEL_COOLDOWN_SEC:
            return False

        window = 300  # 5 min
        lst = self._channel_burst.get(cid, [])
        lst = [x for x in lst if t - x < window]
        if len(lst) >= MAX_REPLIES_PER_CHANNEL_PER_5MIN:
            self._channel_burst[cid] = lst
            return False

        lst.append(t)
        self._channel_burst[cid] = lst
        self._last_user[uid] = t
        self._last_channel[cid] = t
        return True

    def _looks_like_command(self, content: str) -> bool:
        # slash commands komen niet als message content binnen, maar prefix-commands wel
        return content.startswith(("!", ".", "?", "$", "/"))

    def _meaningful(self, content: str) -> bool:
        content = content.strip()
        if len(content) < MIN_MESSAGE_CHARS:
            return False
        letters = sum(c.isalnum() for c in content)
        return letters >= 6

    def _reply_chance_for_channel(self, message: discord.Message) -> float:
        name = self._channel_name(message)
        if name == NSFW_CHANNEL_NAME:
            return NSFW_REPLY_CHANCE
        return DEFAULT_REPLY_CHANCE

    def _clean_mention(self, content: str) -> str:
        if not self.bot.user:
            return content.strip()
        return (
            content.replace(f"<@{self.bot.user.id}>", "")
                   .replace(f"<@!{self.bot.user.id}>", "")
                   .strip()
        )

    def _is_quota_429(self, e: Exception) -> bool:
        s = str(e)
        s_low = s.lower()
        return (
            "429" in s
            or "resource_exhausted" in s_low
            or "quota" in s_low
            or "rate limit" in s_low
            or "too many requests" in s_low
        )

    async def _ask_ai(self, message: discord.Message, prompt: str) -> str:
        # Verwacht dat ai_gemini.py bot.gemini_answer zet
        if not hasattr(self.bot, "gemini_answer"):
            return "⚠️ Gemini helper ontbreekt. Check cogs/ai_gemini.py setup()."

        return await self.bot.gemini_answer(message.author.display_name, prompt)

    async def _reply(self, message: discord.Message, prompt: str, include_context: bool = True):
        async with message.channel.typing():
            try:
                text = await self._ask_ai(message, prompt)
            except Exception as e:
                # ✅ Bij 429/quota: niets zeggen, en ambient even pauzeren
                if self._is_quota_429(e):
                    self._quota_block_until = self._now() + QUOTA_BACKOFF_SEC
                    return

                # Andere fouten (handig om te debuggen)
                await message.reply(
                    f"😅 Ambient AI fout: `{type(e).__name__}: {e}`",
                    mention_author=False
                )
                return

        if not text:
            return

        if len(text) > 1900:
            text = text[:1900] + "…"

        await message.reply(text, mention_author=False)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # laat andere commands normaal werken
        await self.bot.process_commands(message)

        if not self._is_text_channel(message.channel):
            return

        content = (message.content or "").strip()
        if not content or self._looks_like_command(content):
            return

        # 1) Altijd reageren op @mention (overal)
        if self.bot.user and self.bot.user in message.mentions:
            if self._cooldown_ok(message):
                cleaned = self._clean_mention(content)
                if not cleaned:
                    cleaned = "Yo! Waarmee kan ik helpen?"
                await self._reply(message, cleaned, include_context=True)
            return

        # 2) Altijd reageren als iemand replyt op een botbericht (overal)
        # Let op: reference.resolved is niet altijd gevuld → we fetchen het bericht indien nodig
        if message.reference and message.reference.message_id:
            try:
                ref_msg = message.reference.resolved
                if ref_msg is None:
                    ref_msg = await message.channel.fetch_message(message.reference.message_id)

                if (
                    isinstance(ref_msg, discord.Message)
                    and self.bot.user
                    and ref_msg.author
                    and ref_msg.author.id == self.bot.user.id
                ):
                    if self._cooldown_ok(message) and self._meaningful(content):
                        await self._reply(message, content, include_context=True)
                    return
            except Exception:
                # als fetch faalt: doe niets
                pass

        # 3) Ambient meepraten: alleen in allowed kanalen, nooit in blocked kanalen
        if self._is_blocked(message):
            return

        if self._is_allowed(message) and self._meaningful(content):
            chance = self._reply_chance_for_channel(message)
            if random.random() < chance:
                if self._cooldown_ok(message):
                    await self._reply(message, content, include_context=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(AmbientAI(bot))
