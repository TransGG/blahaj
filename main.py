#!/usr/bin/env python3

import discord
import os

intents = discord.Intents.default()
client = discord.Client(intents=intents)
commands = discord.app_commands.CommandTree(client)

command_registration_guild = discord.Object(id=os.environ["DISCORD_DEV_GUILD"]) if os.environ["DISCORD_DEV_GUILD"] else None

@client.event
async def on_ready():
	print(f"[3665] Logged in as {client.user} ({client.user.id})")

	await commands.sync(guild=command_registration_guild)

	print(f"[3665] Synced commands")

@client.event
async def on_interaction(interaction):
	if interaction.type != discord.InteractionType.component:
		return

	custom_id = interaction.data.get("custom_id", "") or ""

	if not custom_id.startswith("request-role-"):
		return

	# TODO: make more role request types possible
	# TODO: dynamic (random-selected?) questions

	questions_view = discord.ui.View()

	questions_view.add_item(discord.ui.Select(
		placeholder="Are you allowed to use voice messages to bypass automoderator rules?",
		options=[
			discord.SelectOption(label="Yes"),
			discord.SelectOption(label="No"),
		],
		row=0
	))
	questions_view.add_item(discord.ui.Select(
		placeholder="If you break server rules using voice messages, will moderators be more lenient?",
		options=[
			discord.SelectOption(label="Yes"),
			discord.SelectOption(label="No, they will be the same as if I were using text"),
			discord.SelectOption(label="No, they will be harsher than if I were using text"),
		],
		row=1
	))

	await interaction.response.send_message(
		ephemeral=True,
		content="To make sure you've read our rules, please answer these questions...\n"
				"1. **Are you allowed to use voice messages to bypass automoderator rules?**\n"
				"2. **If you break server rules using voice messages, will moderators be more lenient?**\n",
		view=questions_view
	)

@commands.command(
	name="send",
	description="Send a message which has the role button",
	guild=command_registration_guild,
)
async def send(interaction):
	get_role_button = discord.ui.Button(
		style=discord.ButtonStyle.green,
		label="Get the role",
		custom_id="request-role-voice-message",
	)

	await interaction.response.send_message(
		content="Press the button to get the role",
		ephemeral=False,
		view=discord.ui.View().add_item(get_role_button)
	)

client.run(os.environ["DISCORD_TOKEN"])
