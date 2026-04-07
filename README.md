# Discord Trigger Bot

Bot que responde automáticamente a mensajes que contengan ciertas palabras,
con un 33% de probabilidad de responder y eligiendo al azar entre una lista
de respuestas configurables.

---

## Archivos

```
bot.py            ← código principal del bot
requirements.txt  ← dependencias Python
render.yaml       ← configuración para Render.com
data.json         ← se crea automáticamente al correr el bot
```

---

## Configuración inicial (bot.py)

### 1. Tu ID de Discord (whitelist)

Abre `bot.py` y reemplaza el número en la línea:
```python
WHITELIST = [
    123456789012345678,  # <-- Reemplaza con tu ID real
]
```

**Cómo obtener tu ID:**
1. En Discord, ve a Ajustes → Avanzado → activa "Modo desarrollador"
2. Haz clic derecho sobre tu nombre → "Copiar ID"

---

## Deploy en Render.com

### Paso 1 — Subir a GitHub
1. Crea un repositorio en GitHub (puede ser privado)
2. Sube los 3 archivos: `bot.py`, `requirements.txt`, `render.yaml`

### Paso 2 — Crear el servicio en Render
1. Ve a https://render.com y crea una cuenta
2. New → **Background Worker**
3. Conecta tu repositorio de GitHub
4. Render detectará el `render.yaml` automáticamente

### Paso 3 — Agregar el token de Discord
1. En el dashboard de Render, ve a tu servicio → **Environment**
2. Agrega la variable:
   - Key: `DISCORD_TOKEN`
   - Value: el token de tu bot (ver abajo)

### Paso 4 — Crear el bot en Discord
1. Ve a https://discord.com/developers/applications
2. New Application → ponle nombre
3. Bot → "Add Bot" → copia el **Token**
4. En OAuth2 → URL Generator:
   - Scopes: `bot`
   - Permissions: `Send Messages`, `Read Messages/View Channels`, `Read Message History`
5. Copia la URL generada y ábrela para invitar el bot a tu servidor

---

## Comandos disponibles (solo whitelist)

| Comando | Descripción | Ejemplo |
|---|---|---|
| `!addtrigger <palabra> <respuesta>` | Crea un trigger nuevo | `!addtrigger buenas buenos días` |
| `!addreply <palabra> <respuesta>` | Agrega respuesta a un trigger | `!addreply hola qué onda` |
| `!delreply <palabra> <número>` | Elimina respuesta por número | `!delreply hola 2` |
| `!deltrigger <palabra>` | Elimina un trigger completo | `!deltrigger buenas` |
| `!listtriggers` | Lista todos los triggers | `!listtriggers` |
| `!bothelp` | Muestra ayuda | `!bothelp` |

---

## Cómo funciona la lógica

```
Mensaje recibido
      │
      ▼
¿Contiene algún trigger?
      │
     SÍ
      │
      ▼
Random 0–100%
  ├─ 0–32%  → Responde (elige respuesta al azar de la lista)
  └─ 33–99% → Ignora el mensaje
```

Solo se aplica el **primer trigger** que coincida en el mensaje.

---

## Correr localmente (opcional)

```bash
pip install -r requirements.txt
set DISCORD_TOKEN=tu_token_aqui   # Windows
python bot.py
```
