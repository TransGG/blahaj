#!/usr/bin/env python3

import discord
from discord import app_commands
import os

intents = discord.Intents.default()
client = discord.Client(intents=intents)
commands = app_commands.CommandTree(client)

@client.event
async def on_ready():
	print(f"Logged in as {client.user} ({client.user.id})")

client.run(os.environ["DISCORD_TOKEN"])
