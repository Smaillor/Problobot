# 📦 Imports
import discord
from discord.ext import commands, tasks
import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import asyncio

# ⚙️ Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Suivi des membres
bot = commands.Bot(command_prefix="!", intents=intents)

# 🆔 Identifiants des salons et rôles (à personnaliser)
ROLE_MEMBER_ID = 1370055375402963114
WELCOME_CHANNEL_ID = 1370056858534019092
LOG_CHANNEL_ID = 1370056844269322332

# 📋 Utilitaire : envoyer un message dans le salon de logs
async def log_message(message):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(message)

# 🟢 Événement : bot prêt
@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching, name="Problèmes de Ping")
    await bot.change_presence(status=discord.Status.dnd, activity=activity)
    print(f"✅ Problobot connecté en tant que {bot.user}")
    await log_message(f"Le bot {bot.user} est maintenant en ligne.")

# 👋 Événement : nouveau membre
@bot.event
async def on_member_join(member):
    role = member.guild.get_role(ROLE_MEMBER_ID)
    if role:
        await member.add_roles(role)
        print(f"🎉 Rôle '{role.name}' attribué à {member.name}")

    embed = discord.Embed(
        title="🎉 Bienvenue sur le serveur !",
        description=(
            f"Salut {member.mention}, ravi de t'avoir parmi nous ! 🎈\n\n"
            "N'oublie pas de lire les règles dans <#1370055393501249629> "
            "et de prendre tes rôles dans <#1370056832282005645>.\nAmuse-toi bien ! 😄"
        ),
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else "")
    embed.set_footer(text=f"Membre n°{len(member.guild.members)}")
    await log_message(f"🎉 {member.name} a rejoint le serveur !")

    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

# 🚪 Événement : départ membre
@bot.event
async def on_member_remove(member):
    embed = discord.Embed(
        title="👋 Un membre nous quitte...",
        description=f"{member.name} a quitté le serveur.\nÀ une prochaine fois !",
        color=discord.Color.red()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else "")
    await log_message(f"👋 {member.name} a quitté le serveur.")

    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

# 🗑️ Événement : message supprimé
@bot.event
async def on_message_delete(message):
    log_msg = f"🗑️ Message supprimé dans {message.channel.mention} par {message.author.name} : {message.content}"
    await log_message(log_msg)

# ✏️ Événement : message modifié
@bot.event
async def on_message_edit(before, after):
    if before.content != after.content:
        log_msg = (
            f"✏️ Message modifié dans {before.channel.mention} par {before.author.name}.\n"
            f"Avant : {before.content}\nAprès : {after.content}"
        )
        await log_message(log_msg)

# 🔧 Commandes de modération
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 {amount} messages supprimés.", delete_after=5)
    await log_message(f"🧹 {amount} messages supprimés dans {ctx.channel.mention} par {ctx.author.name}.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Aucune raison spécifiée."):
    await member.kick(reason=reason)
    await ctx.send(f"🔨 {member.mention} a été expulsé. Raison : {reason}")
    await log_message(f"🔨 {member.name} a été expulsé par {ctx.author.name}. Raison : {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Aucune raison spécifiée."):
    await member.ban(reason=reason)
    await ctx.send(f"⛔ {member.mention} a été banni. Raison : {reason}")
    await log_message(f"⛔ {member.name} a été banni par {ctx.author.name}. Raison : {reason}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="Aucune raison spécifiée."):
    try:
        await member.send(
            f"⚠️ Tu as reçu un avertissement sur **{ctx.guild.name}**.\n\n**Raison :** {reason}"
        )
    except discord.Forbidden:
        await ctx.send(f"❌ Impossible d’envoyer un message privé à {member.mention}.")

    embed = discord.Embed(
        title="⚠️ Avertissement",
        description=f"{member.mention} a été averti.",
        color=discord.Color.orange()
    )
    embed.add_field(name="Raison", value=reason, inline=False)
    embed.set_footer(text=f"Averti par {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed)
    await log_message(f"⚠️ {member.name} a été averti par {ctx.author.name}. Raison : {reason}")

# 📛 Liste de mots interdits (à personnaliser)
blacklisted_words = ["pd", "fdp", "fils de pute", "pédophile", "furry", "zoophile", "nigga", "negre", "negro", "cul", "enculé", "fesse", "seins", "boulard", "pipi", "caca", "bite", "zizi", "beuteu", "dick", "suck", "boycott", "putain"]

@bot.event
async def on_message(message):
    # Ignore les messages du bot lui-même
    if message.author.bot:
        return

    # Check de la blacklist
    for word in blacklisted_words:
        if word.lower() in message.content.lower():
            await message.delete()
            warning = f"🚫 {message.author.name}, ton message a été supprimé car il contenait un mot interdit."
            await message.channel.send(warning, delete_after=5)
            await log_message(f"🚫 Message supprimé de {message.author.name} : contenait un mot interdit.")
            return  # Ne pas traiter d'autres commandes si supprimé

    await bot.process_commands(message)  # Nécessaire pour que les commandes continuent de marcher

# 🔍 Commandes d'information
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title="Infos utilisateur", color=discord.Color.blue())
    embed.set_thumbnail(url=member.avatar.url if member.avatar else "")
    embed.add_field(name="Nom", value=member.name, inline=True)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Rejoint le", value=member.joined_at.strftime("%d %B %Y"), inline=False)
    embed.add_field(
        name="Rôles",
        value=", ".join([role.name for role in member.roles if role.name != "@everyone"]),
        inline=False
    )
    await ctx.send(embed=embed)

# ⚠️ Commandes administratives
@bot.command()
@commands.has_permissions(administrator=True)
async def restart(ctx):
    await log_message(f"🔁 {ctx.author.name} a redémarré le bot.")
    await ctx.send("🔁 Redémarrage du bot en cours...")
    await bot.close()
    os.execv(sys.executable, ['python'] + sys.argv)

@bot.command()
@commands.has_permissions(administrator=True)
async def stop(ctx):
    await log_message(f"🛑 {ctx.author.name} a arrêté le bot.")
    await ctx.send("🛑 Arrêt du bot en cours...")
    await bot.close()

# 🤝 Commandes utilitaires

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong ! Latence : {latency} ms")
    print(f"{ctx.author.name} a exécuté la commande !ping")

@bot.command()
async def dailysongs(ctx):
    url = "https://kworb.net/spotify/country/fr_daily.html"
    response = requests.get(url)
    response.encoding = 'utf-8'  # Force l'encodage correct
    if response.status_code != 200:
        await ctx.send("❌ Impossible d'accéder au site kworb.")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")  # Trouve le tableau avec les classements
    rows = table.find_all("tr")[1:11]  # On saute l'entête, on prend les 10 suivants

    top10 = []
    for i, row in enumerate(rows, 1):
        cols = row.find_all("td")
        if len(cols) >= 6:
            artist = cols[2].text.strip().replace("w/", "ft.")
            title = cols[3].text.strip()
            streams = cols[6].text.strip().replace(",", " ")  # Pour éviter les virgules mal affichées
            top10.append(f"**{i}.** {artist} - ({streams} streams aujourd'hui)")


    result = "\n".join(top10)
    await ctx.send(f"🎧 **Top 10 Spotify France aujourd'hui :**\n{result}")

@bot.event
async def on_voice_state_update(member, before, after):
    CREATE_CHANNEL_ID = 1370499650989068409  # Remplace par l'ID de ton salon "+Créer un vocal"
    MAX_USERS = 5  # Limite du salon vocal

    if after.channel and after.channel.id == CREATE_CHANNEL_ID:
        category = after.channel.category

        # Créer le salon vocal temporaire
        overwrites = {
            member: discord.PermissionOverwrite(
                manage_channels=True,
                connect=True,
                move_members=True,
                mute_members=True,
                deafen_members=True
            ),
            category.guild.default_role: discord.PermissionOverwrite(connect=True)
        }

        temp_channel = await category.guild.create_voice_channel(
            name=f"🔊・{member.display_name}",
            category=category,
            overwrites=overwrites,
            user_limit=MAX_USERS
        )

        # Déplacer le membre dedans
        await member.move_to(temp_channel)

        # Supprimer le salon s'il devient vide
        async def delete_if_empty(channel):
            await bot.wait_until_ready()
            while True:
                await asyncio.sleep(1)
                if len(channel.members) == 0:
                    await channel.delete()
                    break

        bot.loop.create_task(delete_if_empty(temp_channel))

@bot.command(name="aide")
async def aide(ctx):
    embed = discord.Embed(
        title="📖 Commandes du bot",
        description="Voici les commandes que tu peux utiliser :",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="🎧 !dailysongs",
        value="Affiche le top 10 des sons les plus streamés aujourd'hui sur Spotify France",
        inline=False
    )
    embed.add_field(
        name="❓ !help",
        value="Affiche ce message d'aide",
        inline=False
    )
    embed.add_field(
        name="🏓 !ping",
        value="Affiche la latence du bot",
        inline=False
    )
    embed.add_field(
        name="📍 !userinfo <username>",
        value="Affiche le profil de la personne choisie",
        inline=False
    )
    await ctx.send(embed=embed)


# 🚀 Démarrage du bot (⚠️ Ne pas mettre le token ici en dur)
bot.run("MTM3MDA2NTYwODMwOTM0MjI2MA.Grc-QF.oOSc0Zy5FESqox_VvxGTHSsCe5_1nwwsqYqkCI")  # Remplace par ton token via une variable d’environnement ou un fichier .env sécurisé