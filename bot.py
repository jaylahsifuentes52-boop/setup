import os
import json
import asyncio
from pathlib import Path

import discord
from discord.ext import commands
from aiohttp import web

TOKEN = os.getenv("DISCORD_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
DATA_FILE = Path("saved_videos.json")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set in the Render environment.")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def load_saved():
    if not DATA_FILE.exists():
        return {}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_saved(data):
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


saved_videos = load_saved()


class SaveVideoModal(discord.ui.Modal, title="Save a video"):
    video_url = discord.ui.TextInput(
        label="Video link",
        placeholder="Paste the video URL here...",
        required=True,
        max_length=1000,
    )
    note = discord.ui.TextInput(
        label="Name / note",
        placeholder="Optional name for the saved video",
        required=False,
        max_length=100,
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)

        guild_saved = saved_videos.setdefault(guild_id, [])
        entry = {
            "name": str(self.note.value).strip() or "Saved video",
            "url": str(self.video_url.value).strip(),
            "user_id": user_id,
            "user": str(interaction.user),
        }
        guild_saved.append(entry)
        save_saved(saved_videos)

        await interaction.response.send_message(
            f"✅ Saved **{entry['name']}**.\n{entry['url']}",
            ephemeral=True,
        )


class SaveVideoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Save Video",
        emoji="🎥",
        style=discord.ButtonStyle.primary,
        custom_id="save_video_button",
    )
    async def save_video(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SaveVideoModal())

    @discord.ui.button(
        label="Saved Videos",
        emoji="📁",
        style=discord.ButtonStyle.secondary,
        custom_id="saved_videos_button",
    )
    async def saved_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = str(interaction.guild_id)
        items = saved_videos.get(guild_id, [])

        if not items:
            await interaction.response.send_message(
                "📁 There are no saved videos yet.", ephemeral=True
            )
            return

        lines = []
        for i, item in enumerate(items[-15:], start=max(1, len(items) - 14)):
            lines.append(f"**{i}. {item['name']}**\n{item['url']}")

        embed = discord.Embed(
            title="📁 Saved Videos",
            description="\n\n".join(lines),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


def find_channel(guild, name):
    return discord.utils.get(guild.text_channels, name=name)


async def get_or_create_category(guild, name):
    category = discord.utils.get(guild.categories, name=name)
    if category is None:
        category = await guild.create_category(name)
    return category


async def get_or_create_text(guild, name, category=None):
    channel = discord.utils.get(guild.text_channels, name=name)
    if channel is None:
        channel = await guild.create_text_channel(name, category=category)
    elif category is not None and channel.category != category:
        await channel.edit(category=category)
    return channel


async def get_or_create_voice(guild, name, category=None):
    channel = discord.utils.get(guild.voice_channels, name=name)
    if channel is None:
        channel = await guild.create_voice_channel(name, category=category)
    elif category is not None and channel.category != category:
        await channel.edit(category=category)
    return channel


@bot.tree.command(name="setup", description="Set up the server layout and Save Video panel.")
@commands.guild_only()
async def setup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You need **Manage Server** to run `/setup`.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True, thinking=True)
    guild = interaction.guild

    # Layout based on the Discord server shown in the uploaded reference video.
    general = await get_or_create_category(guild, "IN GAME")
    for name in ["chat", "media", "memes"]:
        await get_or_create_text(guild, name, general)

    voice = await get_or_create_category(guild, "VOICE CHAT")
    for name in ["Main VC", "1 on 1 VC", "Chill VC", "Sleeping VC"]:
        await get_or_create_voice(guild, name, voice)

    modding = await get_or_create_category(guild, "Modding stuff")
    for name in ["apks", "libs", "your-modded-apks", "games-you-want-modded"]:
        await get_or_create_text(guild, name, modding)

    anti = await get_or_create_category(guild, "Anti cheat remover")
    await get_or_create_text(guild, "imh-remover", anti)

    info = await get_or_create_text(guild, "status-meaning")
    welcome = await get_or_create_text(guild, "welcome")

    save_channel = await get_or_create_text(guild, "save-video")

    embed = discord.Embed(
        title="🎥 Video Saver",
        description=(
            "Use the buttons below to save video links for this server.\n\n"
            "🎥 **Save Video** — save a video URL and an optional name.\n"
            "📁 **Saved Videos** — view the saved links.\n\n"
            "This bot stores the **link**, not a copy of the video."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Configured with /setup")

    await save_channel.send(embed=embed, view=SaveVideoView())

    await interaction.followup.send(
        "✅ Setup complete! I created the server layout and the **#save-video** panel.",
        ephemeral=True,
    )


@bot.tree.command(name="saved-videos", description="Show saved video links for this server.")
@commands.guild_only()
async def saved_videos_command(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    items = saved_videos.get(guild_id, [])
    if not items:
        await interaction.response.send_message(
            "📁 There are no saved videos yet.", ephemeral=True
        )
        return

    lines = []
    for i, item in enumerate(items[-20:], start=max(1, len(items) - 19)):
        lines.append(f"**{i}. {item['name']}**\n{item['url']}")

    embed = discord.Embed(
        title="📁 Saved Videos",
        description="\n\n".join(lines),
        color=discord.Color.blurple(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.event
async def on_ready():
    bot.add_view(SaveVideoView())
    try:
        synced = await bot.tree.sync()
        print(f"Logged in as {bot.user}. Synced {len(synced)} slash commands.")
    except Exception as exc:
        print(f"Slash-command sync error: {exc}")


async def health(request):
    return web.Response(text="Discord bot is online.")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"HTTP server listening on port {PORT}")


async def main():
    await start_web_server()
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
