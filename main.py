#!/usr/bin/env python3

import discord
import os
import random
import asyncio
import json

intents = discord.Intents.default()
client = discord.Client(intents=intents)
commands = discord.app_commands.CommandTree(client)

command_registration_guild = discord.Object(id=os.environ["DISCORD_DEV_GUILD"]) if os.environ["DISCORD_DEV_GUILD"] else None

role_to_give = discord.Object(id=os.environ["DISCORD_ROLE_ID"])
contact_staff_id = os.environ["DISCORD_CONTACT_STAFF_ID"]

rules = f"""
# I want to send voice messages!
This channel will allow you to give yourself the <@&{role_to_give.id}> role, which will allow you to send voice messages in text chats.

This feature is most commonly used as a disability aid for those who are struggling to type. However, all server members are welcome to use it.

## There are a few rules specifically associated with access to this feature:
### Mockery is not tolerated
- This is a server full of unique people with unique voices, and many of the people here are uncomfortable/dysphoric about said voices. To that end, to keep our members safe, any kind of mockery based on someone's voice and/or their use of this feature will not be tolerated.
- Please report this if you see it, we want this place to be safe for everyone to have a voice!

### Follow the server rules
- Moderation of voice messages in chat will be stricter than text messages, due to the increased difficulty in doing so. Please make sure you are following all of the server rules when using this feature.
- Remember that if you see someone doing something they shouldn't be, you can report the message (Right Click -> Apps -> Report Message) to have a staff member take a look.

### And one last thing...
- **ANY violation of Rule 1 (Hate Has No Home Here) or Rule 2 (No Age-Restricted, Obscene, Shocking, Gory, or Violent Content) when using voice messages will result in a server ban.**

If you agree to these rules, please click the button below to give yourself the <@&{role_to_give.id}> role. If you later want it removed please contact us in <#{contact_staff_id}>.
"""

def load_responses():
	try:
		with open("responses.json", "r") as response_file:
			return json.load(response_file)
	except FileNotFoundError:
		return {}

responses = load_responses()

questions = {
	"bypass-automod": {
		"question": "Are you allowed to use voice messages to bypass automoderator rules?",
		"correct": "No",
		"others": ["Yes"]
	},
	"lenient-mods": {
		"question": "If you break server rules using voice messages, will moderators be more lenient?",
		"correct": "No, they will be harsher than if I were using text",
		"others": ["Yes", "No, they will be the same as if I were using text"]
	},
}

class Question(discord.ui.Select):
	def __init__(self, question: str):
		self.question_id = question
		answers = [questions[question]["correct"]] + questions[question]["others"]
		answer_select_options = list(map(lambda answer: discord.SelectOption(label=answer), answers))
		random.shuffle(answer_select_options)
		super().__init__(
			placeholder=questions[question]["question"],
			options=answer_select_options
		)
		self.__answered = asyncio.get_running_loop().create_future()

	def prompt(self):
		return questions[self.question_id]["question"]

	async def callback(self, interaction: discord.Interaction):
		await interaction.response.defer()

		for option in self.options:
			if option.value in self.values:
				option.default = True
			else:
				option.default = False

		if not self.__answered.done():
			self.__answered.set_result(True)

	async def answered(self):
		await self.__answered

	def correct(self):
		if not self.__answered.done():
			return None

		return self.values[0] == questions[self.question_id]["correct"]

class SubmitButton(discord.ui.Button):
	def __init__(self):
		super().__init__(
			label="I'm done, give me the role!",
			style=discord.ButtonStyle.green,
			disabled=True
		)
		self.__pressed = asyncio.get_running_loop().create_future()

	def activate(self):
		self.disabled = False

	async def pressed(self):
		return await self.__pressed

	async def callback(self, interaction: discord.Interaction):
		await interaction.response.defer()
		if not self.__pressed.done():
			self.__pressed.set_result(True)

def save_responses():
	with open("responses.json", "w") as response_file:
		json.dump(responses, response_file)

def has_user_responded(user):
	return str(user.id) in responses

def write_user_response(user, questions, answers):
	question_ids = map(lambda question: question.question_id, questions)
	question_answer_pairs = zip(question_ids, answers)
	responses[str(user.id)] = dict(question_answer_pairs)

	save_responses()

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

	custom_id_parts = custom_id.split(":")

	if custom_id_parts[0] == "request-role":
		assert len(custom_id_parts) == 2
		return await handle_request_role_button(interaction, *custom_id_parts[1:])


async def handle_request_role_button(interaction, requested_role):
	if has_user_responded(interaction.user):
		return await interaction.response.send_message(
			ephemeral=True,
			content=f"Sorry, you only get one chance at this. If you need to try again, please create a ticket in <#{contact_staff_id}>"
		)

	questions_view = discord.ui.View()

	question1 = Question("bypass-automod")
	question2 = Question("lenient-mods")

	submit_button = SubmitButton()

	questions_view.add_item(question1)
	questions_view.add_item(question2)
	questions_view.add_item(submit_button)

	response_content = (
		"To make sure you've read our rules, please answer these questions...\n"
		f"1. **{question1.prompt()}**\n"
		f"2. **{question2.prompt()}**\n"
		"\n"
		"*Psst, be careful when answering: you can only answer these questions once!*"
	)

	await interaction.response.send_message(
		ephemeral=True,
		content=response_content,
		view=questions_view
	)

	await asyncio.gather(
		question1.answered(),
		question2.answered()
	)

	submit_button.activate()

	await interaction.edit_original_response(view=questions_view)

	await submit_button.pressed()

	answers_correct = [ # Cannot be done in a single step to allow people to change answer...
		question1.correct(),
		question2.correct()
	]

	assert isinstance(interaction.user, discord.Member)

	if has_user_responded(interaction.user):
		return await interaction.edit_original_response(
			view=None,
			content=f"Aren't you speedy! Unfortunately, you've already answered the questions, so I can't let you answer again. if you need more help, please create a ticket in <#{contact_staff_id}>"
		)

	write_user_response(interaction.user, [question1, question2], answers_correct)

	if not all(answers_correct):
		# Bail
		return await interaction.edit_original_response(
			view=None,
			content=f"Sorry, that's not quite right... if you need more help, please create a ticket in <#{contact_staff_id}>"
		)

	await interaction.edit_original_response(
		view=None,
		content=f"Thanks for reading our rules, I've given you the role. Thank you for being a part of TransPlace!"
	)

	await interaction.user.add_roles(role_to_give)


async def handle_question_answer(interaction, requested_role, question):
	print(f"got {question} answer for {requested_role}")
	print(interaction.data)

@commands.command(
	name="send",
	description="Send a message which has the role button",
	guild=command_registration_guild,
)
@discord.app_commands.checks.has_permissions(administrator=True)
async def send(interaction):
	get_role_button = discord.ui.Button(
		style=discord.ButtonStyle.green,
		label="Give me the role",
		custom_id="request-role:voice-message",
	)

	await interaction.response.send_message(
		content=rules,
		ephemeral=False,
		view=discord.ui.View().add_item(get_role_button)
	)

@commands.command(
	name="reload",
	description="Reload responses from the file, useful for if you want to wipe someone's record clean",
	guild=command_registration_guild,
)
@discord.app_commands.checks.has_permissions(administrator=True)
async def reload(interaction):
	responses = load_responses()

	await interaction.response.send_message(
		content="Done!",
		ephemeral=True,
	)

client.run(os.environ["DISCORD_TOKEN"])
