import os
import json
import random
import asyncio
import io
import aiohttp
import discord
from discord.ext import commands
from groq import Groq

# ─── Config ───────────────────────────────────────────────────────────────────
TOKEN        = os.environ.get("DISCORD_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
DATA_FILE    = "data.json"

WHITELIST = [
    786993411605135411,  # <-- Tu ID de Discord
]

DEFAULT_DATA = {
    "triggers": {
        "hola":    ["que tal", "no", "a bueno"],
        "gracias": ["de nada", "claro", "np"],
        "adios":   ["bye", "hasta luego", "chao"],
    }
}

# ─── Groq client ──────────────────────────────────────────────────────────────
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ─── Pollinations helper ──────────────────────────────────────────────────────
async def generar_imagen(descripcion: str) -> bytes:
    seed = random.randint(1, 999999)
    prompt_encoded = descripcion.replace(" ", "%20")
    url = (
        f"https://image.pollinations.ai/prompt/{prompt_encoded}"
        f"?width=1024&height=1024&nologo=true&seed={seed}"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            resp.raise_for_status()
            return await resp.read()

# ─── Carga / guarda JSON ──────────────────────────────────────────────────────
def load_data():
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_DATA.copy()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if not os.path.isfile(DATA_FILE):
    save_data(DEFAULT_DATA)

# ─── Bot ──────────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def is_whitelisted(user_id: int) -> bool:
    return user_id in WHITELIST

# ─── Eventos ──────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"[OK] Bot conectado como {bot.user}")
    print(f"[OK] Groq: {'activo' if groq_client else 'sin API key'}")
    print(f"[OK] Modelo texto: llama-3.3-70b-versatile")
    print(f"[OK] Imágenes: Pollinations.AI (gratis, sin key)")
    print(f"[OK] Triggers: {list(load_data()['triggers'].keys())}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)
    if message.content.startswith("!"):
        return

    data        = load_data()
    content_low = message.content.lower()

    for trigger, responses in data["triggers"].items():
        if trigger.lower() in content_low:
            if random.random() < 0.33:
                await message.reply(random.choice(responses))
            break

# ─── Comando !Ulucerebro ──────────────────────────────────────────────────────
@bot.command(name="Ulucerebro")
async def ulucerebro(ctx, *, pregunta: str = None):
    """
    Responde cualquier pregunta usando Groq (llama-3.3-70b-versatile).
    Uso: !Ulucerebro que es un agujero negro?
    """
    if not pregunta:
        await ctx.send("Escríbeme algo después del comando. Ej: `!Ulucerebro que es un agujero negro?`")
        return

    if not groq_client:
        await ctx.send("La IA no está configurada. Falta la variable `GROQ_API_KEY`.")
        return

    async with ctx.typing():
        try:
            loop = asyncio.get_event_loop()
            respuesta = await loop.run_in_executor(
                None,
                lambda: groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Eres Ulucerebro, un asistente inteligente y directo dentro de un servidor de Discord. "
                                "Responde siempre en español, de forma clara y concisa. "
                                "No uses listas largas ni respuestas muy extensas a menos que sea necesario. "
                                "Adapta tu tono al contexto: casual si la pregunta es informal, preciso si es técnica."
                            ),
                        },
                        {"role": "user", "content": pregunta},
                    ],
                    max_tokens=512,
                    temperature=0.7,
                ),
            )
            texto = f"ulu dice: {respuesta.choices[0].message.content.strip()}"

            if len(texto) > 1900:
                texto = texto[:1900] + "...\n*(respuesta recortada)*"

            await ctx.reply(texto)

        except Exception as e:
            await ctx.send(f"Error al conectar con la IA: `{e}`")

# ─── Comando !uluimg ──────────────────────────────────────────────────────────
@bot.command(name="uluimg")
async def uluimg(ctx, *, descripcion: str = None):
    """
    Genera una imagen con IA a partir de una descripción (Pollinations.AI).
    Uso: !uluimg un gato astronauta en la luna
    """
    if not descripcion:
        await ctx.send("Dime qué imagen quieres. Ej: `!uluimg un dragón en el espacio`")
        return

    async with ctx.typing():
        try:
            imagen_bytes = await generar_imagen(descripcion)
            archivo = discord.File(
                fp=io.BytesIO(imagen_bytes),
                filename="uluimg.png",
            )
            await ctx.reply(f'🎨 **"{descripcion}"**', file=archivo)

        except asyncio.TimeoutError:
            await ctx.send("La generación tardó demasiado, intenta de nuevo.")
        except Exception as e:
            await ctx.send(f"Error generando la imagen: `{e}`")

# ─── Comandos de gestión (solo whitelist) ─────────────────────────────────────
@bot.command(name="addtrigger")
async def add_trigger(ctx, trigger: str, *, respuesta: str):
    if not is_whitelisted(ctx.author.id): await ctx.send("No tienes permiso."); return
    data    = load_data()
    trigger = trigger.lower()
    if trigger in data["triggers"]:
        await ctx.send(f"`{trigger}` ya existe. Usa `!addreply` para agregar respuestas."); return
    data["triggers"][trigger] = [respuesta]
    save_data(data)
    await ctx.send(f"Trigger `{trigger}` creado.")

@bot.command(name="addreply")
async def add_reply(ctx, trigger: str, *, respuesta: str):
    if not is_whitelisted(ctx.author.id): await ctx.send("No tienes permiso."); return
    data    = load_data()
    trigger = trigger.lower()
    if trigger not in data["triggers"]:
        await ctx.send(f"`{trigger}` no existe. Usa `!addtrigger` primero."); return
    data["triggers"][trigger].append(respuesta)
    save_data(data)
    await ctx.send(f"Respuesta agregada a `{trigger}`. Total: {len(data['triggers'][trigger])}")

@bot.command(name="delreply")
async def del_reply(ctx, trigger: str, indice: int):
    if not is_whitelisted(ctx.author.id): await ctx.send("No tienes permiso."); return
    data    = load_data()
    trigger = trigger.lower()
    if trigger not in data["triggers"]:
        await ctx.send(f"`{trigger}` no existe."); return
    responses = data["triggers"][trigger]
    if indice < 1 or indice > len(responses):
        await ctx.send(f"Índice inválido. `{trigger}` tiene {len(responses)} respuesta(s)."); return
    removed = responses.pop(indice - 1)
    save_data(data)
    await ctx.send(f"Eliminada de `{trigger}`: *{removed}*")

@bot.command(name="deltrigger")
async def del_trigger(ctx, trigger: str):
    if not is_whitelisted(ctx.author.id): await ctx.send("No tienes permiso."); return
    data    = load_data()
    trigger = trigger.lower()
    if trigger not in data["triggers"]:
        await ctx.send(f"`{trigger}` no existe."); return
    del data["triggers"][trigger]
    save_data(data)
    await ctx.send(f"Trigger `{trigger}` eliminado.")

@bot.command(name="listtriggers")
async def list_triggers(ctx):
    if not is_whitelisted(ctx.author.id): await ctx.send("No tienes permiso."); return
    data = load_data()
    if not data["triggers"]:
        await ctx.send("No hay triggers."); return
    lines = ["**Triggers:**\n"]
    for trigger, responses in data["triggers"].items():
        lines.append(f"**`{trigger}`** ({len(responses)} respuesta(s)):")
        for i, r in enumerate(responses, 1):
            lines.append(f"  {i}. {r}")
        lines.append("")
    await ctx.send("\n".join(lines))

@bot.command(name="purge")
async def purge_messages(ctx, cantidad: int):
    if not is_whitelisted(ctx.author.id): await ctx.send("No tienes permiso."); return
    if cantidad <= 0:
        await ctx.send("Por favor, ingresa una cantidad mayor a 0."); return
    try:
        deleted = await ctx.channel.purge(limit=cantidad + 1)
        msg = await ctx.send(f"✅ Se han borrado {len(deleted) - 1} mensajes.")
        await asyncio.sleep(3)
        await msg.delete()
    except discord.Forbidden:
        await ctx.send("No tengo permisos para borrar mensajes en este canal.")
    except discord.HTTPException as e:
        await ctx.send(f"Ocurrió un error al intentar borrar mensajes: `{e}`")

@bot.command(name="bothelp")
async def bot_help(ctx):
    if not is_whitelisted(ctx.author.id): await ctx.send("No tienes permiso."); return
    await ctx.send("""**Comandos:**
`!Ulucerebro <pregunta>` — Pregúntale a la IA (llama-3.3-70b)
`!uluimg <descripción>` — Genera una imagen con IA
`!purge <cantidad>` — Borra una cantidad de mensajes
`!addtrigger <palabra> <respuesta>` — Crea trigger
`!addreply <palabra> <respuesta>` — Agrega respuesta
`!delreply <palabra> <número>` — Elimina respuesta
`!deltrigger <palabra>` — Elimina trigger
`!listtriggers` — Lista triggers""")

# ─── Arranque ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not TOKEN:
        print("[ERROR] DISCORD_TOKEN no configurado.")
        exit(1)
    bot.run(TOKEN)
