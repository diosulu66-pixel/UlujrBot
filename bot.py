import os
import json
import random
import discord
from discord.ext import commands
from groq import Groq

# ─── Config ───────────────────────────────────────────────────────────────────
TOKEN = os.environ.get("DISCORD_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
DATA_FILE = "data.json"

WHITELIST = [
    123456789012345678,  # <-- Tu ID de Discord
]

DEFAULT_DATA = {
    "triggers": {
        "hola": ["que tal", "no", "a bueno"],
        "gracias": ["de nada", "claro", "np"],
        "adios": ["bye", "hasta luego", "chao"],
    }
}

# ─── Groq client ──────────────────────────────────────────────────────────────
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

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
    print(f"[OK] Triggers: {list(load_data()['triggers'].keys())}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)
    if message.content.startswith("!"):
        return

    data = load_data()
    content_lower = message.content.lower()

    for trigger, responses in data["triggers"].items():
        if trigger.lower() in content_lower:
            if random.random() < 0.33:
                await message.reply(random.choice(responses))
            break

# ─── Comando !Ulucerebro ──────────────────────────────────────────────────────
@bot.command(name="Ulucerebro")
async def ulucerebro(ctx, *, pregunta: str = None):
    """
    Responde cualquier pregunta usando IA de Groq.
    Uso: !Ulucerebro que es un agujero negro?
    """
    if not pregunta:
        await ctx.send("Escríbeme algo después del comando. Ej: `!Ulucerebro que es un agujero negro?`")
        return

    if not groq_client:
        await ctx.send("La IA no está configurada. Falta la variable `GROQ_API_KEY` en Railway.")
        return

    async with ctx.typing():
        try:
            respuesta = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
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
            )
            texto = respuesta.choices[0].message.content.strip()

            # Discord tiene límite de 2000 caracteres por mensaje
            if len(texto) > 1900:
                texto = texto[:1900] + "...\n*(respuesta recortada)*"

            await ctx.reply(texto)

        except Exception as e:
            await ctx.send(f"Error al conectar con la IA: `{e}`")


# ─── Comandos de gestión (solo whitelist) ─────────────────────────────────────
@bot.command(name="addtrigger")
async def add_trigger(ctx, trigger: str, *, respuesta: str):
    if not is_whitelisted(ctx.author.id):
        await ctx.send("No tienes permiso."); return
    data = load_data()
    trigger = trigger.lower()
    if trigger in data["triggers"]:
        await ctx.send(f"`{trigger}` ya existe. Usa `!addreply` para agregar respuestas."); return
    data["triggers"][trigger] = [respuesta]
    save_data(data)
    await ctx.send(f"Trigger `{trigger}` creado.")

@bot.command(name="addreply")
async def add_reply(ctx, trigger: str, *, respuesta: str):
    if not is_whitelisted(ctx.author.id):
        await ctx.send("No tienes permiso."); return
    data = load_data()
    trigger = trigger.lower()
    if trigger not in data["triggers"]:
        await ctx.send(f"`{trigger}` no existe. Usa `!addtrigger` primero."); return
    data["triggers"][trigger].append(respuesta)
    save_data(data)
    await ctx.send(f"Respuesta agregada a `{trigger}`. Total: {len(data['triggers'][trigger])}")

@bot.command(name="delreply")
async def del_reply(ctx, trigger: str, indice: int):
    if not is_whitelisted(ctx.author.id):
        await ctx.send("No tienes permiso."); return
    data = load_data()
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
    if not is_whitelisted(ctx.author.id):
        await ctx.send("No tienes permiso."); return
    data = load_data()
    trigger = trigger.lower()
    if trigger not in data["triggers"]:
        await ctx.send(f"`{trigger}` no existe."); return
    del data["triggers"][trigger]
    save_data(data)
    await ctx.send(f"Trigger `{trigger}` eliminado.")

@bot.command(name="listtriggers")
async def list_triggers(ctx):
    if not is_whitelisted(ctx.author.id):
        await ctx.send("No tienes permiso."); return
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

@bot.command(name="bothelp")
async def bot_help(ctx):
    if not is_whitelisted(ctx.author.id):
        await ctx.send("No tienes permiso."); return
    await ctx.send("""**Comandos:**
`!Ulucerebro <pregunta>` — Pregúntale a la IA
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
