# Discord Save Video Bot — Render

This bot adds:

- `/setup` — creates a Discord layout based on the uploaded reference video.
- `#save-video` — a panel with **Save Video** and **Saved Videos** buttons.
- `/saved-videos` — lists saved video links.
- Persistent `saved_videos.json` storage.
- An HTTP health server for Render.
- Token loaded only from the `DISCORD_TOKEN` environment variable.

## Important

The bot saves **video links**, not downloaded copies of videos.

## Render setup

1. Upload these files to your GitHub repository:
   - `bot.py`
   - `requirements.txt`
   - `render.yaml` (optional)

2. On Render, create a **Web Service**.

3. Build Command:
   `pip install -r requirements.txt`

4. Start Command:
   `python bot.py`

5. Add this environment variable:
   - Key: `DISCORD_TOKEN`
   - Value: your Discord bot token

Do not put your real bot token in `bot.py`, GitHub, or this ZIP.

## Discord permissions

Invite the bot with the permissions it needs to create categories/channels and send messages.
The `/setup` command requires the person running it to have **Manage Server**.

## Commands

- `/setup`
- `/saved-videos`

After `/setup`, open `#save-video` and press **Save Video**.
