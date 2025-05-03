import os
from dotenv import load_dotenv

from flask import Flask
from threading import Thread

import discord
from discord.ext import commands

app = Flask('')


@app.route('/')
def home():
    return "✅ SprachCafé Bot is running!"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Begrüßungsnachrichten speichern, um sie später zu löschen
last_greetings = {}


@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")


@bot.event
async def on_member_join(member):
    # Rolle "Neu" geben
    neu_role = discord.utils.get(member.guild.roles, name="Neu")
    if neu_role and neu_role not in member.roles:
        await member.add_roles(neu_role)

    # Begrüßung im Channel posten
    vorstellung_channel = discord.utils.get(member.guild.text_channels,
                                            name="vorstellung")
    if vorstellung_channel:
        welcome_msg = await vorstellung_channel.send(
            f"👋 Willkommen {member.mention} auf dem Server!\n\n"
            "Um Zugriff zu bekommen, gib bitte deinen **Vor- und Nachnamen** ein (z. B. `Anna Müller`)."
        )
        last_greetings[member.id] = welcome_msg


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.name == "vorstellung":
        name_parts = message.content.strip().split()

        if len(name_parts) >= 2:
            full_name = " ".join(name_parts[:2])
            member_role = discord.utils.get(message.guild.roles, name="Member")
            neu_role = discord.utils.get(message.guild.roles, name="Neu")
            allgemein_channel = discord.utils.get(message.guild.text_channels,
                                                  name="allgemein")
            logging_channel = discord.utils.get(message.guild.text_channels,
                                                name="logging")

            # Nickname setzen
            try:
                await message.author.edit(nick=full_name)
            except discord.Forbidden:
                print("❌ Bot darf Nickname nicht ändern.")

            # Rollen ändern
            if member_role:
                await message.author.add_roles(member_role)
            if neu_role and neu_role in message.author.roles:
                await message.author.remove_roles(neu_role)

            # Begrüßung löschen
            greet_msg = last_greetings.get(message.author.id)
            if greet_msg:
                try:
                    await greet_msg.delete()
                except:
                    pass
                del last_greetings[message.author.id]

            # Nachricht des Users löschen
            try:
                await message.delete()
            except:
                pass

            # Nachricht im #allgemein Channel
            if allgemein_channel:
                await allgemein_channel.send(
                    f"{message.author.mention} ist jetzt verifiziert ✅")

            # Log im #logging Channel
            if logging_channel:
                embed = discord.Embed(
                    title="✅ Neuer User verifiziert",
                    description=(f"**Name:** {full_name}\n"
                                 f"**User:** {message.author.mention}\n"
                                 f"**ID:** `{message.author.id}`"),
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow())
                embed.set_footer(text="SprachCafé Verifizierung")
                try:
                    await logging_channel.send(embed=embed)
                except:
                    print("⚠️ Konnte nicht in #logging schreiben.")

        else:
            await message.channel.send(
                f"{message.author.mention} ❗ Bitte gib **Vor- und Nachnamen** ein."
            )

    await bot.process_commands(message)


keep_alive()

bot.run(os.getenv("BOT_TOKEN"))
