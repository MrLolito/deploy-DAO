import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

# Lista global para almacenar los lanzamientos de monedas
lanzamientos = []

# Variable para almacenar el chat_id del grupo
chat_id_grupo = None

# Comando para registrar el grupo
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global chat_id_grupo
    chat_id_grupo = update.message.chat_id  # Capturar el chat_id del grupo
    await update.message.reply_text("✅ Bot configurado para este grupo. Notificaciones activadas.")

# Comando para mostrar los lanzamientos agendados
async def show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if lanzamientos:
        mensaje = "*Próximos Lanzamientos de Criptomonedas:* 📅\n" + "\n".join(
            [f"{i + 1}. {lanzamiento['nombre']} - {lanzamiento['hora'].strftime('%d/%m/%Y %H:%M')}" for i, lanzamiento in enumerate(lanzamientos)]
        )
    else:
        mensaje = "🔄 *No hay lanzamientos agendados.*\nUsa el comando /add para agregar uno nuevo."
    await update.message.reply_text(mensaje, parse_mode=ParseMode.MARKDOWN)

# Comando para agregar un lanzamiento
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global lanzamientos
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ *Error:* Debes proporcionar el nombre de la moneda y la fecha/hora.\n\nEjemplo: `/add BTC 03/12/2024 18:30`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    
    try:
        nombre = " ".join(context.args[:-2])
        hora_lanzamiento = datetime.strptime(" ".join(context.args[-2:]), "%d/%m/%Y %H:%M")
        lanzamientos.append({"nombre": nombre, "hora": hora_lanzamiento, "notificaciones": {"1h": False, "30m": False, "10m": False}})
        lanzamientos.sort(key=lambda x: x["hora"])  # Ordenar por fecha
        await update.message.reply_text(f"✅ *Lanzamiento agendado:*\n`{nombre}` el `{hora_lanzamiento.strftime('%d/%m/%Y %H:%M')}`", parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await update.message.reply_text(
            "❌ *Error:* Fecha/hora inválida.\nAsegúrate de usar el formato `dd/mm/yyyy hh:mm`.\n\nEjemplo: `/add BTC 03/12/2024 18:30`",
            parse_mode=ParseMode.MARKDOWN,
        )

# Comando para borrar un lanzamiento
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global lanzamientos
    if not context.args:
        await update.message.reply_text("❌ *Error:* Debes indicar el número del lanzamiento a borrar.\n\nEjemplo: `/delete 1`", parse_mode=ParseMode.MARKDOWN)
        return
    try:
        indice = int(context.args[0]) - 1
        if 0 <= indice < len(lanzamientos):
            lanzamiento_eliminado = lanzamientos.pop(indice)
            await update.message.reply_text(f"🗑️ *Lanzamiento borrado:*\n`{lanzamiento_eliminado['nombre']}` el `{lanzamiento_eliminado['hora'].strftime('%d/%m/%Y %H:%M')}`", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("⚠️ *Índice fuera de rango.*\nRevisa la lista con /show y prueba de nuevo.", parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await update.message.reply_text("❌ *Error:* El índice debe ser un número válido.\n\nEjemplo: `/delete 1`", parse_mode=ParseMode.MARKDOWN)

# Función que verifica lanzamientos y envía recordatorios
async def check(context: ContextTypes.DEFAULT_TYPE) -> None:
    global lanzamientos, chat_id_grupo
    if not chat_id_grupo:
        return  # Si el chat_id no está configurado, no hacer nada

    ahora = datetime.now()
    lanzamientos_pendientes = []
    for lanzamiento in lanzamientos:
        tiempo_restante = lanzamiento["hora"] - ahora

        # Enviar notificaciones en diferentes momentos
        if timedelta(hours=1) >= tiempo_restante > timedelta(minutes=59) and not lanzamiento["notificaciones"]["1h"]:
            await context.bot.send_message(
                chat_id=chat_id_grupo,
                text=f"⏰ *Recordatorio:* Falta 1 hora para el lanzamiento de:\n`{lanzamiento['nombre']}` el `{lanzamiento['hora'].strftime('%d/%m/%Y %H:%M')}`",
                parse_mode=ParseMode.MARKDOWN,
            )
            lanzamiento["notificaciones"]["1h"] = True

        if timedelta(minutes=30) >= tiempo_restante > timedelta(minutes=29) and not lanzamiento["notificaciones"]["30m"]:
            await context.bot.send_message(
                chat_id=chat_id_grupo,
                text=f"⏰ *Recordatorio:* Faltan 30 minutos para el lanzamiento de:\n`{lanzamiento['nombre']}` el `{lanzamiento['hora'].strftime('%d/%m/%Y %H:%M')}`",
                parse_mode=ParseMode.MARKDOWN,
            )
            lanzamiento["notificaciones"]["30m"] = True

        if timedelta(minutes=10) >= tiempo_restante > timedelta(minutes=9) and not lanzamiento["notificaciones"]["10m"]:
            await context.bot.send_message(
                chat_id=chat_id_grupo,
                text=f"⏰ *Último aviso:* Faltan 10 minutos para el lanzamiento de:\n`{lanzamiento['nombre']}` el `{lanzamiento['hora'].strftime('%d/%m/%Y %H:%M')}`",
                parse_mode=ParseMode.MARKDOWN,
            )
            lanzamiento["notificaciones"]["10m"] = True

        # Mantener solo lanzamientos que aún no han pasado
        if ahora < lanzamiento["hora"]:
            lanzamientos_pendientes.append(lanzamiento)

    # Actualizar la lista global de lanzamientos
    lanzamientos = lanzamientos_pendientes

# Configuración del bot
def main():
    # Reemplaza 'TOKEN' con tu token del bot de Telegram
    TOKEN = "7981011283:AAFQHjt2LSNm10jOkJww0rubtTI-ZcuP92s"

    # Crear la aplicación con JobQueue habilitada
    application = Application.builder().token(TOKEN).build()

    # Agregar handlers
    application.add_handler(CommandHandler("start", start))  # Para registrar el grupo
    application.add_handler(CommandHandler("show", show))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("delete", delete))

    # Agregar tarea periódica para verificar lanzamientos
    application.job_queue.run_repeating(check, interval=60, first=10)

    # Iniciar el bot
    application.run_polling()

if __name__ == "__main__":
    main()
