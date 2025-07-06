import asyncio
import json
import logging
import discord
from discord.ext import commands
import os
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import random
import xml.etree.ElementTree as ET

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
server_id = os.getenv("SERVER_ID")
DATA_FILE = "dias_desempleo.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        dias_usuarios = json.load(f)
else:
    dias_usuarios = {}


def actualizar_dias(user_id, hora_entrada, hora_salida, duracion):
    dias_usuarios.setdefault(user_id, {
        "first_seen": hora_entrada,
        "last_seen": hora_salida,
        "name": "",
        "minutes": 0
    })

    # Actualizamos
    dias_usuarios[user_id]["first_seen"] = hora_entrada
    dias_usuarios[user_id]["last_seen"] = hora_salida
    dias_usuarios[user_id]["minutes"] += duracion

    with open(DATA_FILE, "w") as f:
        json.dump(dias_usuarios, f, indent=4)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode="w")
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=server_id))
    print(f"{bot.user} ha llegado para recaudar.")

@bot.event
async def on_member_join(member):
    await member.send(f"Bienvenido a la cola del INEM {member.name}")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    user_id = str(member.id) # Conseguimos el id del usuario que ha entrado

    #Agregar estructura del usuario
    dias_usuarios.setdefault(user_id, {
        "first_seen": 0,
        "last_seen": 0,
        "name": member.name,
        "minutes": 0
    })

    if before.channel is None and after.channel is not None:
        print("Ha entrado")
        if dias_usuarios[user_id]["first_seen"] != int(time.time()):
            dias_usuarios[user_id]["first_seen"] = int(time.time())
            dias_usuarios[user_id]["name"] = member.name

    if before.channel is not None and after.channel is None:
        print("Ha salido")
        hora_salida = int(time.time())
        if dias_usuarios[user_id]["last_seen"] != hora_salida:
            dias_usuarios[user_id]["last_seen"] = hora_salida
            hora_entrada = dias_usuarios[user_id]["first_seen"]
            duracion_conectado =  round((hora_salida - hora_entrada) / 60,  2)
            actualizar_dias(user_id, hora_entrada, hora_salida, duracion_conectado)

            minutos = round(dias_usuarios[user_id]["minutes"] / 60, 2)
            segundos = round(dias_usuarios[user_id]["minutes"] % 60, 2)
            rango = ""
            if minutos >= 21600:
                rango = "Rinconer"
            elif minutos >= 14400:
                rango = "alexgamer" 
            elif minutos >= 7200:
                rango = "streamer"

            system_channel = member.guild.system_channel
            if system_channel:
                await system_channel.send(
                    f"{member.mention} ha trabajado hoy un total de {minutos} minutos y {segundos} segundos. Tu rango es: {rango}"
                )

@bot.event
async def on_message(msg):
    if msg.author.id == bot.user.id:
        return
    else:
        if msg.content.startswith("!"):
            try:
                await bot.process_commands(msg)
                return
            except commands.CommandNotFound:
                await msg.channel.send(f"Este comando no está afiliado en nuestra base de datos. Trabaja.")

    await bot.process_commands(msg)

@bot.command()
async def hola(ctx):
    await ctx.send(f"No hables y trabaja {ctx.author.mention}!")

@bot.command()
async def participo(ctx):
    num_rand = random.randint(1, 5)
    print(num_rand)
    if num_rand == 1:
        await ctx.send(f"{ctx.author.mention}, ¡Enhorabuena, has ganado un trabajo no remunerado de media joranada (12 horas)! Disfrutalo.")
    elif num_rand == 2:
        if ctx.author.voice and ctx.author.voice.channel:
            await ctx.author.edit(voice_channel=None)
            await ctx.send(f"{ctx.author.mention}, has sido enviado al paro. Pronta recuperación.")
        else:
            await ctx.send(f"{ctx.author.mention}, no estás en un canal de voz. No se puede ejecutar el despido.")
    elif num_rand == 3:
        if ctx.author.voice:
            canal = ctx.author.voice.channel
            if ctx.voice_client is None:
                await canal.connect()
                voice_client =  ctx.voice_client
                
                audio_url = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_7aaa62b0a4.mp3?filename=fart-83471.mp3"

                voice_client.play(discord.FFmpegPCMAudio(audio_url), after=lambda e: print("Reproducción finalizada."))

                while voice_client.is_playing():
                    await discord.utils.sleep_until(voice_client.is_playing())

                await voice_client.disconnect()


@bot.command()
async def limpiar_chat(ctx, cantidad: int = None):
    if ctx.channel.id == 1391446538982527047:
        await ctx.send("A donde vas a borrar el general gilipollas. Anda a trabajar perro muerto")
        return

    if cantidad is not None:
        canal = await ctx.channel.purge(limit=cantidad+1)
        confirm = await ctx.send(f"🧹 Se han eliminado {cantidad} mensajes.")

    else:
        canal = await ctx.channel.purge(limit=None)
        confirm = await ctx.send("🧹 Todos los mensajes han sido eliminados.")

    await asyncio.sleep(3)




bot.run(BOT_TOKEN, log_handler=handler, log_level=logging.DEBUG)