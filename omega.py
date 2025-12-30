import discord
from discord.ext import commands, tasks
import datetime
import re
import asyncio
import textdistance
import math
from collections import defaultdict, deque


class OmegaConfig:
    TOKEN = ''
    LOG_CHANNEL_ID = 
    PREFIX = "dose"
    
    SAFE_DOMAINS = ['discord.gg', 'discord.com', 'youtube.com', 'google.com', 'steamcommunity.com', 'github.com']
    MAX_MENTIONS_LIMIT = 3
    BURST_JOIN_LIMIT = 6 
    BURST_JOIN_WINDOW = 3
    MIN_ACCOUNT_AGE_DAYS = 3
    
    
    MAX_CHANNEL_DELETIONS = 2
    MAX_MEMBER_KICKS = 3
    MAX_ROLE_DELETIONS = 2


intents = discord.Intents.all()
bot = commands.Bot(command_prefix=OmegaConfig.PREFIX, intents=intents, help_command=None)

bot.lockdown_active = False
bot.start_time = datetime.datetime.now()
bot.stats = {"phishing": 0, "raids": 0, "nuke_attempts": 0, "spam": 0}
bot.join_tracker = deque(maxlen=100)
bot.antiflood_cache = defaultdict(lambda: deque(maxlen=5))


bot.admin_actions = defaultdict(lambda: {"channels": 0, "roles": 0, "kicks": 0})



@tasks.loop(seconds=60)
async def reset_admin_actions():
    bot.admin_actions.clear()

@bot.event
async def on_ready():
    print(f"--- ⚠️ DOSEUSER: ISOZ PROTECTOR ONLINE ---")
    reset_admin_actions.start()
    channel = bot.get_channel(OmegaConfig.LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="☢️ ISOZ PROTECTOR: POR DOSEUSER GRADO MILITAR",
            description="**SISTEMA ANTI-RAID & ANTI-NUKE DEFINITIVO**\nNivel de Seguridad: `EXTREMO`",
            color=0x000000,
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="🛡️ Anti-Nuke", value="`ACTIVO`", inline=True)
        embed.add_field(name="⚔️ Anti-Raid", value="`MÁXIMO`", inline=True)
        embed.add_field(name="🧬 Heurística", value="`ALFA-1`", inline=True)
        embed.set_footer(text="Protección Militar por DOSEUSER")
        await channel.send(embed=embed)



async def neutralize_admin(guild, admin, reason):
    
    if admin.id == guild.owner_id: return 
    try:
        await admin.edit(roles=[], reason=f"DETECCIÓN ANTI-NUKE: {reason}")
        bot.stats["nuke_attempts"] += 1
        log_ch = bot.get_channel(OmegaConfig.LOG_CHANNEL_ID)
        if log_ch:
            await log_ch.send(f"🚨 **ALERTA ANTI-NUKE:** Se han retirado los permisos a {admin.mention} por: `{reason}`")
    except:
        pass

@bot.event
async def on_guild_channel_delete(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        user = entry.user
        if user.bot or user.id == channel.guild.owner_id: return
        bot.admin_actions[user.id]["channels"] += 1
        if bot.admin_actions[user.id]["channels"] > OmegaConfig.MAX_CHANNEL_DELETIONS:
            await neutralize_admin(channel.guild, user, "Eliminación masiva de canales")

@bot.event
async def on_guild_role_delete(role):
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        user = entry.user
        if user.bot or user.id == role.guild.owner_id: return
        bot.admin_actions[user.id]["roles"] += 1
        if bot.admin_actions[user.id]["roles"] > OmegaConfig.MAX_ROLE_DELETIONS:
            await neutralize_admin(role.guild, user, "Eliminación masiva de roles")

@bot.event
async def on_member_remove(member):
    async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
        user = entry.user
        if user.bot or user.id == member.guild.owner_id: return
        bot.admin_actions[user.id]["kicks"] += 1
        if bot.admin_actions[user.id]["kicks"] > OmegaConfig.MAX_MEMBER_KICKS:
            await neutralize_admin(member.guild, user, "Expulsión masiva de miembros (Nuke/Pruning)")



@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    await bot.process_commands(message)
    if message.author.guild_permissions.administrator: return

    if bot.lockdown_active:
        await message.delete()
        return

    
    urls = re.findall(r'(https?://[^\s]+)', message.content)
    for url in urls:
        for safe in OmegaConfig.SAFE_DOMAINS:
            sim = textdistance.levenshtein.normalized_similarity(url.lower(), safe)
            if 0.75 <= sim < 1.0:
                await message.delete()
                await message.author.ban(reason="ISOZ: Phishing detectado")
                bot.stats["phishing"] += 1
                return

@bot.event
async def on_member_join(member):
    now = datetime.datetime.now(datetime.timezone.utc)
   
    if (now - member.created_at).days < OmegaConfig.MIN_ACCOUNT_AGE_DAYS:
        try: await member.ban(reason="ISOZ: Anti-Alt (Cuenta < 3 días)"); return
        except: pass

    
    bot.join_tracker.append(now)
    if len(bot.join_tracker) >= OmegaConfig.BURST_JOIN_LIMIT:
        if (bot.join_tracker[-1] - bot.join_tracker[0]).total_seconds() <= OmegaConfig.BURST_JOIN_WINDOW:
            bot.lockdown_active = True
            await member.guild.default_role.edit(permissions=discord.Permissions(send_messages=False), reason="ISOZ: MODO LOCKDOWN")
            bot.stats["raids"] += 1



@bot.command(name="report")
@commands.has_permissions(administrator=True)
async def report(ctx):
    uptime = datetime.datetime.now() - bot.start_time
    embed = discord.Embed(title="☢️ REPORTE TÁCTICO DOSEUSER", color=0xFF0000)
    embed.add_field(name="⏱️ Tiempo Activo", value=str(uptime).split('.')[0], inline=False)
    embed.add_field(name="🛡️ Ataques Anti-Nuke", value=f"`{bot.stats['nuke_attempts']}`", inline=True)
    embed.add_field(name="⚔️ Raids Detenidas", value=f"`{bot.stats['raids']}`", inline=True)
    embed.add_field(name="🚫 Phishing/Links", value=f"`{bot.stats['phishing']}`", inline=True)
    embed.add_field(name="🔒 Modo Lockdown", value="`ACTIVADO`" if bot.lockdown_active else "`DESACTIVADO`", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="disengage")
@commands.has_permissions(administrator=True)
async def disengage(ctx):
    bot.lockdown_active = False
    await ctx.guild.default_role.edit(permissions=discord.Permissions(send_messages=True, connect=True, add_reactions=True))
    await ctx.send("✅ **PROTOCOLO APOCALYPSE FINALIZADO. SERVIDOR RESTAURADO.**")

if __name__ == "__main__":
    bot.run(OmegaConfig.TOKEN)

