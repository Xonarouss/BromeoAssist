import os
import re
import asyncio
import tempfile
import time
import requests
import discord
from discord.ext import commands

VOICE_CHANNEL_NAME = "Praat met BromeoASSIST"

ELEVEN_API = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
DEFAULT_MODEL_ID = "eleven_multilingual_v2"

MAX_TTS_CHARS = 240
TTS_COOLDOWN_SEC = 1.2


def clean_text_for_tts(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"<a?:\w+:\d+>", "", text)          # custom emoji
    text = re.sub(r"`{1,3}.*?`{1,3}", "", text, flags=re.DOTALL)
    text = re.sub(r"https?://\S+", "", text)
    text = text.strip()
    return text


class TTSAutoPlay(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "").strip()

        self._queue: asyncio.Queue[tuple[int, str]] = asyncio.Queue()
        self._worker_task = self.bot.loop.create_task(self._worker())
        self._last_tts = 0.0

    def cog_unload(self):
        try:
            self._worker_task.cancel()
        except Exception:
            pass

    def _now(self) -> float:
        return time.time()

    async def _get_voice_channel(self, guild: discord.Guild) -> discord.VoiceChannel | None:
        for ch in guild.voice_channels:
            if ch.name == VOICE_CHANNEL_NAME:
                return ch
        return None

    async def _ensure_voice(self, guild: discord.Guild) -> discord.VoiceClient | None:
        target = await self._get_voice_channel(guild)
        if not target:
            return None

        vc = guild.voice_client
        if vc and vc.is_connected():
            if vc.channel and vc.channel.id == target.id:
                return vc
            try:
                await vc.move_to(target)
            except Exception:
                pass
            return guild.voice_client

        try:
            return await target.connect()
        except Exception:
            return guild.voice_client

    async def _elevenlabs_tts(self, text: str) -> bytes | None:
        if not self.api_key or not self.voice_id:
            return None

        url = ELEVEN_API.format(voice_id=self.voice_id)
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": DEFAULT_MODEL_ID,
            "voice_settings": {"stability": 0.35, "similarity_boost": 0.85},
        }

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=45)
        except Exception:
            return None

        # Bij rate limits / quota / errors: NIETS zeggen
        if r.status_code in (401, 403, 404, 408, 429, 500, 502, 503, 504):
            return None
        if r.status_code >= 400:
            return None

        return r.content

    async def _play_bytes(self, vc: discord.VoiceClient, audio_bytes: bytes):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio_bytes)
            path = f.name

        try:
            src = discord.FFmpegPCMAudio(path)
            done = asyncio.Event()

            def _after(_err):
                done.set()

            vc.play(src, after=_after)
            await done.wait()
        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    async def _worker(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            guild_id, text = await self._queue.get()
            try:
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue

                vc = await self._ensure_voice(guild)
                if not vc:
                    continue

                audio = await self._elevenlabs_tts(text)
                if not audio:
                    continue

                while vc.is_playing() or vc.is_paused():
                    await asyncio.sleep(0.15)

                await self._play_bytes(vc, audio)
            except Exception:
                pass
            finally:
                self._queue.task_done()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Alleen TTS als BOT zelf praat
        if not message.guild or not self.bot.user:
            return
        if message.author.id != self.bot.user.id:
            return

        if self._now() - self._last_tts < TTS_COOLDOWN_SEC:
            return

        text = clean_text_for_tts(message.content or "")
        if not text:
            return

        text = text[:MAX_TTS_CHARS]
        self._last_tts = self._now()

        await self._queue.put((message.guild.id, text))


async def setup(bot: commands.Bot):
    await bot.add_cog(TTSAutoPlay(bot))
