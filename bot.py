import os
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from dotenv import load_dotenv

# === CARGAR VARIABLES DEL ENTORNO (.env) ===
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
PREMIUM_CHANNEL_ID = int(os.getenv("PREMIUM_CHANNEL_ID"))

# === ESTADOS DE USUARIO ===
usuarios_pendientes = {}  # {user_id: {"status": "..."}} 

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usuarios_pendientes[user_id] = {"status": "inicio"}

    keyboard = [
        [InlineKeyboardButton("📘 Detalles del canal 🔞 ", callback_data="info")],
        [InlineKeyboardButton("💳 Enviar comprobante de pago 📸", callback_data="pago")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 ¡Hola! Bienvenido al Chat de acceso a mi canal premium.\n\n"
        "En este espacio encontrarás toda la informacion para que puedas acceder a mi contenido exclusivo 🔞🔥\n"
        "Puedes elegir una opción para continuar:",
        reply_markup=reply_markup
    )

# === MANEJAR LOS BOTONES ===
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "info":
        usuarios_pendientes[user_id]["status"] = "viendo_info"
        keyboard = [
            [InlineKeyboardButton("💳 Continuar al pago", callback_data="pago")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📘 *Detalles del canal 🔞*\n\n"
            "🔸 El canal ofrece contenido exclusivo para suscriptores.\n"
            "🔸 En el canal encomtrarás mucho contenido, sin censura,🔥 exclusivo⭐ y completo😏! Fotos y videos al momento!📹 Y nudes que me gusta compartirles!🔞 \n"
            "🔸 La suscripción tiene un costo de acceso mensual por solo *$110.00 MXN*.\n\n"
            "🔸 Para obtener acceso, debes enviar una captura de pantalla de la transferencia o de tu comprobante de pago.\n"
            "🔸 Tu suscripcion me ayuda a seguir creciendo como creador de contenido y estar al pendiente de mi comunidad, si te interesa ayudarme y disfrutar de mi contenido continua aqui!😏.\n\n"
            "¿Deseas continuar al proceso de pago o cancelar?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif query.data == "pago":
        usuarios_pendientes[user_id]["status"] = "esperando_comprobante"
        keyboard = [[InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

                # Eliminamos el mensaje anterior del menú (si existía)
        await query.edit_message_text("Procesando información...")

        # Mensaje 1 – Introducción
        await query.message.reply_text(
            "¡Genial! 🥵\n\n"
            "Para unirte es muy sencillo:"
        )

        # Mensaje 2 – Pasos del proceso
        await query.message.reply_text(
            "1️⃣ Realiza tu pago o transferencia 💳\n"
            "2️⃣ Envía una *captura o foto del comprobante de pago* (transferencia o depósito). 📸\n"
            "3️⃣ ¡Listo! ⭐ Una vez enviado, el administrador verificará tu pago y te dará acceso. ℹ️",
            parse_mode="Markdown"
        )

        # Mensaje 3 – Costo
        await query.message.reply_text(
            "💸 *Costo: $110.00 MXN* (pesos mexicanos) por 30 días.",
            parse_mode="Markdown"
        )

        # Mensaje 4 – Información de pago BBVA
        await query.message.reply_text(
            "🪙 *Número de tarjeta (BBVA):*\n"
            "`4815 1630 4314 5997`\n\n"
            "Titular: *Fernando Santiago*",
            parse_mode="Markdown"
        )

        # Mensaje 5 – Opción PayPal
        await query.message.reply_text(
            "💲 También puedes pagar por PayPal:\n"
            "https://paypal.me/SagNando",
            parse_mode="Markdown",
            disable_web_page_preview=False
        )

        # Mensaje 6 – Recordatorio de cancelación
        await query.message.reply_text(
            "💟 *ESPERO TU COMPROBANTE!* \n Si no deseas continuar o suscribirte, puedes *cancelar en cualquier momento*.",
            parse_mode="Markdown",
            reply_markup=reply_markup  # Aquí pones tus botones de “Cancelar” o “Volver al menú”
        )


    elif query.data == "cancelar":
        usuarios_pendientes.pop(user_id, None)
        await query.edit_message_text(
            "🚫 Proceso cancelado. Puedes escribir /start para comenzar de nuevo.😊"
        )

# === RECEPCIÓN DE COMPROBANTE ===
async def recibir_comprobante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in usuarios_pendientes or usuarios_pendientes[user_id]["status"] != "esperando_comprobante":
        await update.message.reply_text("⚠️ No estás en el proceso de envío de comprobante. Escribe /start para comenzar.")
        return

    file_id = update.message.photo[-1].file_id
    usuarios_pendientes[user_id]["status"] = "pendiente_revision"
    usuarios_pendientes[user_id]["file_id"] = file_id

    await update.message.reply_text("✅ Comprobante recibido. El administrador revisará tu pago pronto.")

    admin_msg = (
        f"📩 Nuevo comprobante de {update.effective_user.first_name} "
        f"(@{update.effective_user.username or 'sin_username'})\n"
        f"ID: {user_id}\n\n"
        f"Aprobalo con /aprobar {user_id} o recházalo con /rechazar {user_id}."
    )
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=admin_msg)

# === ADMIN: APROBAR USUARIO ===
async def aprobar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 No tienes permiso para usar este comando.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Uso: /aprobar <id_usuario>")
        return

    user_id = int(args[0])
    try:
        invite = await context.bot.create_chat_invite_link(PREMIUM_CHANNEL_ID, member_limit=1)
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 Tu pago fue aprobado.\n\n👉 Ingresa al canal premium aquí: {invite.invite_link}"
        )
        usuarios_pendientes.pop(user_id, None)
        await update.message.reply_text("✅ Usuario aprobado correctamente.")
    except Exception as e:
        await update.message.reply_text(f"Error al aprobar usuario: {e}")

# === ADMIN: RECHAZAR USUARIO ===
async def rechazar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 No tienes permiso para usar este comando.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Uso: /rechazar <id_usuario>")
        return

    user_id = int(args[0])
    await context.bot.send_message(
        chat_id=user_id,
        text="❌ Tu comprobante fue rechazado. Si crees que es un error, contacta al administrador."
    )
    usuarios_pendientes.pop(user_id, None)
    await update.message.reply_text("🚫 Usuario rechazado.")

# === MAIN ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("aprobar", aprobar))
    app.add_handler(CommandHandler("rechazar", rechazar))
    app.add_handler(CallbackQueryHandler(menu_callback))
    app.add_handler(MessageHandler(filters.PHOTO, recibir_comprobante))

    print("🤖 Bot en ejecución con menú interactivo...")
    app.run_polling()

if __name__ == "__main__":
    main()
