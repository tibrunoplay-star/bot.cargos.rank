import os
import discord
import psycopg
from discord.ext import commands, tasks

TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

GUILD_ID = 1330618861955059882
CANAL_PROMOVIDOS = 1517493761821769848

ROLE_ESTAGIARIO = 1515341566758359202
ROLE_JUNIOR = 1515342092484739083
ROLE_SENIOR = 1515342771773509672
ROLE_VETERANO = 1424109431242625044
ROLE_LENDA = 1517180170975445052

conn = psycopg.connect(DATABASE_URL)

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def determinar_cargo(km):
    if km >= 150000:
        return ROLE_LENDA

    if km >= 90000:
        return ROLE_VETERANO

    if km >= 45000:
        return ROLE_SENIOR

    if km >= 15000:
        return ROLE_JUNIOR

    return ROLE_ESTAGIARIO


@bot.event
async def on_ready():
    print(f"Ligado como {bot.user}")
    verificar_promocoes.start()


@tasks.loop(minutes=5)
async def verificar_promocoes():

    guild = bot.get_guild(GUILD_ID)

    if guild is None:
        return

    canal = guild.get_channel(CANAL_PROMOVIDOS)

    with conn.cursor() as cur:

        cur.execute("""
            SELECT motorista, km
            FROM ranking_total
        """)

        dados = cur.fetchall()

    for motorista, km_total in dados:

        membro = discord.utils.get(
            guild.members,
            name=motorista
        )

        if membro is None:
            continue

        cargo_correto_id = determinar_cargo(km_total)

        cargo_correto = guild.get_role(
            cargo_correto_id
        )

        if cargo_correto is None:
            continue

        cargos_progressao = [
            ROLE_ESTAGIARIO,
            ROLE_JUNIOR,
            ROLE_SENIOR,
            ROLE_VETERANO,
            ROLE_LENDA
        ]

        ja_tem = any(
            role.id == cargo_correto_id
            for role in membro.roles
        )

        if ja_tem:
            continue

        remover = [
            role
            for role in membro.roles
            if role.id in cargos_progressao
        ]

        try:

            if remover:
                await membro.remove_roles(*remover)

            await membro.add_roles(cargo_correto)

            if canal:

                await canal.send(
                    f"🎉 **PROMOÇÃO** 🎉\n\n"
                    f"🚚 {membro.mention}\n"
                    f"⭐ Novo cargo: **{cargo_correto.name}**\n"
                    f"📏 Quilómetros totais: **{km_total:,} km**"
                )

            print(
                f"{motorista} promovido para "
                f"{cargo_correto.name}"
            )

        except Exception as e:
            print(
                f"Erro ao promover "
                f"{motorista}: {e}"
            )


bot.run(TOKEN)
