# BromeoASSIST — Discord bot pakket (lokaal draaien + goedkoop hosten)

Dit project is een modulair Discord-bot starterpakket voor **Bromeo's LOUNGE** met:
- `/ai` (Gemini chat)
- `/image` (OpenAI image gen)
- `/tts` (ElevenLabs text-to-speech)
- `/fortnite` (Fortnite-API.com stats + extra endpoints)
- Muziek via Lavalink (Wavelink)
- `/rebuild` (server rebuild op basis van config)

> **Belangrijk:** zet je API keys **nooit** hardcoded in code. Gebruik `.env`.

---

## 0) Vereisten (Windows stream-PC)
- Python 3.11+ (aanrader)
- Git (optioneel)
- **Docker Desktop** (aanrader) voor Lavalink **of** Java 17+ als je Lavalink zonder Docker wilt draaien.

---

## 1) Installatie (lokaal)
1. Download/clone deze map.
2. Open PowerShell in de projectmap.
3. Maak een virtuele omgeving:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
4. Installeer dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
5. Kopieer `.env.example` naar `.env` en vul je keys in.
6. Start Lavalink (zie stap 2).
7. Start de bot:
   ```powershell
   python bot.py
   ```

---

## 2) Lavalink (muziek) — snelste met Docker
Maak in een aparte map (bijv. `lavalink/`) twee bestanden:

### `docker-compose.yml`
```yaml
services:
  lavalink:
    image: ghcr.io/lavalink-devs/lavalink:4
    container_name: lavalink
    restart: unless-stopped
    ports:
      - "2333:2333"
    volumes:
      - ./application.yml:/opt/Lavalink/application.yml:ro
```

### `application.yml`
```yaml
server:
  port: 2333
lavalink:
  server:
    password: "youshallnotpass"
```

Start:
```powershell
docker compose up -d
```

---

## 3) Discord bot aanmaken (kort)
- Maak een bot in Discord Developer Portal
- Zet **Privileged Gateway Intents** aan als je later message events nodig hebt
- Nodig de bot uit met permissions voor slash commands + manage roles/channels (alleen als je `/rebuild` gebruikt)

---

## 4) Hosting (goedkoop)
- **Hetzner** (kleine VPS) is vaak goedkoop en stabiel
- **Oracle Cloud Free** (kan gratis, maar setup is wat lastiger)
- **Fly.io** / **Railway** kan ook, maar muziek (voice) is soms tricky door netwerk/UDP

Tip: op een VPS draai je Lavalink + bot in Docker Compose.

---

## 5) Config: server rebuild
Pas `config/server_config.json` aan en run `/rebuild plan` om te previewen, en daarna `/rebuild apply CONFIRM_CODE`.
