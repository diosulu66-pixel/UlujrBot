import discord
import json
import os
import random
from discord.ext import commands

# ─── Config ───────────────────────────────────────────────────────────────────
TOKEN = os.environ.get("DISCORD_TOKEN", "")
DATA_FILE = "data.json"

# IDs de Discord de los usuarios con permisos de admin
WHITELIST = [
    786993411605135411,  # <-- Reemplaza con tu ID de Discord
    # 987654321098765432,  # Agrega más IDs aquí
]

# ─── Datos por defecto ────────────────────────────────────────────────────────
DEFAULT_DATA = {
    "triggers": {
        "hola": ["que tal", "no", "a bueno"],
        "gracias": ["de nada", "claro", "np"],
        "adios": ["bye", "hasta luego", "chao"],
    }
}

# ─── Carga / guarda JSON ──────────────────────────────────────────────────────
def load_data():
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_DATA.copy()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Inicializar archivo si no existe
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
    print(f"[OK] Bot conectado como {bot.user} (ID: {bot.user.id})")
    print(f"[OK] Triggers cargados: {list(load_data()['triggers'].keys())}")

@bot.event
async def on_message(message):
    # Ignorar mensajes del propio bot
    if message.author == bot.user:
        return

    # Procesar comandos primero
    await bot.process_commands(message)

    # No responder si el mensaje ES un comando
    if message.content.startswith("!"):
        return

    data = load_data()
    content_lower = message.content.lower()

    for trigger, responses in data["triggers"].items():
        if trigger.lower() in content_lower:
            # 33% de probabilidad de responder
            if random.random() < 0.33:
                reply = random.choice(responses)
                await message.reply(reply)
            break  # Solo aplica el primer trigger que coincida

# ─── Comandos (solo whitelist) ────────────────────────────────────────────────

@bot.command(name="addtrigger")
async def add_trigger(ctx, trigger: str, *, respuesta: str):
    """
    Crea un nuevo trigger con su primera respuesta.
    Uso: !addtrigger buenas buenos días amigo
    """
    if not is_whitelisted(ctx.author.id):
        await ctx.send("❌ No tienes permiso para usar este comando.")
        return

    data = load_data()
    trigger = trigger.lower()
    if trigger in data["triggers"]:
        await ctx.send(f"⚠️ El trigger `{trigger}` ya existe. Usa `!addreply` para agregar respuestas.")
        return

    data["triggers"][trigger] = [respuesta]
    save_data(data)
    await ctx.send(f"✅ Trigger `{trigger}` creado con la respuesta: *{respuesta}*")


@bot.command(name="addreply")
async def add_reply(ctx, trigger: str, *, respuesta: str):
    """
    Agrega una respuesta nueva a un trigger existente.
    Uso: !addreply hola qué onda
    """
    if not is_whitelisted(ctx.author.id):
        await ctx.send("❌ No tienes permiso para usar este comando.")
        return

    data = load_data()
    trigger = trigger.lower()
    if trigger not in data["triggers"]:
        await ctx.send(f"❌ El trigger `{trigger}` no existe. Usa `!addtrigger` para crearlo.")
        return

    data["triggers"][trigger].append(respuesta)
    save_data(data)
    total = len(data["triggers"][trigger])
    await ctx.send(f"✅ Respuesta agregada a `{trigger}`. Total de respuestas: {total}")


@bot.command(name="delreply")
async def del_reply(ctx, trigger: str, indice: int):
    """
    Elimina una respuesta de un trigger por número (empieza en 1).
    Uso: !delreply hola 2
    """
    if not is_whitelisted(ctx.author.id):
        await ctx.send("❌ No tienes permiso para usar este comando.")
        return

    data = load_data()
    trigger = trigger.lower()
    if trigger not in data["triggers"]:
        await ctx.send(f"❌ El trigger `{trigger}` no existe.")
        return

    responses = data["triggers"][trigger]
    if indice < 1 or indice > len(responses):
        await ctx.send(f"❌ Índice inválido. El trigger `{trigger}` tiene {len(responses)} respuesta(s).")
        return

    removed = responses.pop(indice - 1)
    save_data(data)
    await ctx.send(f"🗑️ Respuesta eliminada de `{trigger}`: *{removed}*")


@bot.command(name="deltrigger")
async def del_trigger(ctx, trigger: str):
    """
    Elimina un trigger completo con todas sus respuestas.
    Uso: !deltrigger hola
    """
    if not is_whitelisted(ctx.author.id):
        await ctx.send("❌ No tienes permiso para usar este comando.")
        return

    data = load_data()
    trigger = trigger.lower()
    if trigger not in data["triggers"]:
        await ctx.send(f"❌ El trigger `{trigger}` no existe.")
        return

    del data["triggers"][trigger]
    save_data(data)
    await ctx.send(f"🗑️ Trigger `{trigger}` eliminado.")


@bot.command(name="listtriggers")
async def list_triggers(ctx):
    """
    Muestra todos los triggers y sus respuestas.
    Uso: !listtriggers
    """
    if not is_whitelisted(ctx.author.id):
        await ctx.send("❌ No tienes permiso para usar este comando.")
        return

    data = load_data()
    if not data["triggers"]:
        await ctx.send("📭 No hay triggers configurados.")
        return

    lines = ["**📋 Triggers configurados:**\n"]
    for trigger, responses in data["triggers"].items():
        lines.append(f"**`{trigger}`** ({len(responses)} respuesta(s)):")
        for i, r in enumerate(responses, 1):
            lines.append(f"  {i}. {r}")
        lines.append("")

    await ctx.send("\n".join(lines))


@bot.command(name="bothelp")
async def bot_help(ctx):
    """Muestra los comandos disponibles."""
    if not is_whitelisted(ctx.author.id):
        await ctx.send("❌ No tienes permiso para usar este comando.")
        return

    msg = """**🤖 Comandos del bot:**

`!addtrigger <palabra> <respuesta>` — Crea un trigger nuevo
`!addreply <palabra> <respuesta>` — Agrega respuesta a trigger existente
`!delreply <palabra> <número>` — Elimina una respuesta por número
`!deltrigger <palabra>` — Elimina un trigger completo
`!listtriggers` — Lista todos los triggers y respuestas

**Probabilidad de respuesta:** 33% por mensaje que contenga el trigger."""

    await ctx.send(msg)


# ─── Arranque ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not TOKEN:
        print("[ERROR] Variable DISCORD_TOKEN no configurada.")
        exit(1)
    bot.run(TOKEN)
