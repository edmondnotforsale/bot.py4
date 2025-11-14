from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from telegram.error import BadRequest

# ---------------- CONFIG ----------------
TOKEN = "8472477362:AAHHJRATWscrF_FGe-wE8PrD4JqKtc9bAVg"  # Token del bot da BotFather
OWNER_ID = 5702717491              # Il tuo ID Telegram (numerico)
# ----------------------------------------

user_data = {}
orders = []

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "N/A"
    
    # Se sei tu, mostra il tuo ID
    if user_id == OWNER_ID:
        await update.message.reply_text(
            f"👋 Ciao Admin!\n\n"
            f"🆔 Il tuo ID è: `{user_id}`\n"
            f"📱 Username: @{username}\n\n"
            f"Usa /admin per vedere gli ordini\n"
            f"Usa /clear per cancellare gli ordini",
            parse_mode="Markdown"
        )
    
    keyboard = [
        [InlineKeyboardButton("WONKA CHOCOLATE", callback_data="prodotto_WONKA_CHOCOLATE")],
        [InlineKeyboardButton("DRY", callback_data="prodotto_DRY")],
        [InlineKeyboardButton("FROZEN", callback_data="prodotto_FROZEN")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Benvenuto! Scegli un prodotto:", reply_markup=reply_markup)

# ---------- CALLBACK PRODOTTO ----------
async def handle_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product = query.data.replace("prodotto_", "")
    user_id = query.from_user.id
    user_data[user_id] = {"product": product, "stage": "telegram_id"}
    await query.message.reply_text(f"Hai scelto {product}.\n\n📱 Inserisci il tuo ID Telegram (username o @username):")

# ---------- HANDLER TESTO UNIFICATO ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_data:
        return

    stage = user_data[user_id].get("stage")

    if stage == "telegram_id":
        telegram_id = update.message.text.strip()
        if not telegram_id:
            await update.message.reply_text("Per favore inserisci un ID Telegram valido.")
            return
        user_data[user_id]["telegram_id"] = telegram_id
        user_data[user_id]["stage"] = "quantity"
        await update.message.reply_text("Perfetto! Ora inserisci la quantità desiderata (numero):")

    elif stage == "quantity":
        if not update.message.text.isdigit():
            await update.message.reply_text("Per favore inserisci un numero valido per la quantità.")
            return
        user_data[user_id]["quantity"] = int(update.message.text)
        user_data[user_id]["stage"] = "address"
        await update.message.reply_text("Ottimo! Ora inserisci l'indirizzo completo 🏠:")

    elif stage == "address":
        user_data[user_id]["address"] = update.message.text
        user_data[user_id]["stage"] = "time"

        keyboard = []
        for hour in range(10, 20):
            keyboard.append([InlineKeyboardButton(f"{hour}:00 - {hour+1}:00", callback_data=f"time_{hour}-{hour+1}")])
        await update.message.reply_text("Scegli la fascia oraria per la consegna:", reply_markup=InlineKeyboardMarkup(keyboard))

# ---------- CALLBACK ORARIO ----------
async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in user_data or user_data[user_id].get("stage") != "time":
        return
    user_data[user_id]["time"] = query.data.replace("time_", "")
    
    # Salva l'ordine
    order_data = user_data[user_id].copy()
    order_data["user_id"] = user_id  # Salva anche l'ID numerico
    orders.append(order_data)

    # messaggio all'utente
    await query.message.reply_text("✅ Ordine ricevuto! Ti contatteremo a breve per la conferma.")

    # messaggio a te (OWNER_ID) con gestione errori
    data = user_data[user_id]
    
    # Escape dei caratteri speciali per Markdown
    def escape_markdown(text):
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = str(text).replace(char, f'\\{char}')
        return text
    
    msg = (
        f"📦 *Nuovo ordine ricevuto:*\n\n"
        f"👤 ID Telegram: {escape_markdown(data['telegram_id'])}\n"
        f"🆔 User ID: {user_id}\n"
        f"🏠 Indirizzo: {escape_markdown(data['address'])}\n"
        f"🕓 Fascia oraria: {data['time']}\n"
        f"📦 Prodotto: {data['product']}\n"
        f"🔢 Quantità: {data['quantity']}\n"
    )
    
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=msg, parse_mode="Markdown")
        print(f"✅ Notifica inviata all'admin per ordine di User ID: {user_id}")
    except BadRequest as e:
        print(f"⚠️ Impossibile inviare notifica all'admin: {e}")
        print(f"💡 OWNER_ID attuale: {OWNER_ID}")
        print("💡 Assicurati che questo sia IL TUO ID Telegram!")
        print("💡 Usa /myid nel bot per scoprire il tuo vero ID")

    del user_data[user_id]

# ---------- ADMIN ----------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Non hai i permessi per accedere al pannello admin.")
        return
    if not orders:
        await update.message.reply_text("📭 Nessun ordine ricevuto.")
        return
    text = "📋 *Ordini ricevuti:*\n\n"
    for i, o in enumerate(orders, start=1):
        text += (
            f"{i}) {o['product']} x{o['quantity']}\n"
            f"👤 ID: {o['telegram_id']}\n"
            f"🆔 User ID: `{o.get('user_id', 'N/A')}`\n"
            f"⏰ Orario: {o['time']}\n"
            f"🏠 Indirizzo: {o['address']}\n\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

async def clear_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Solo l'admin può cancellare gli ordini.")
        return
    orders.clear()
    await update.message.reply_text("🧹 Tutti gli ordini sono stati cancellati.")

# ---------- COMANDO PER OTTENERE IL PROPRIO ID ----------
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "N/A"
    first_name = update.message.from_user.first_name or "N/A"
    
    await update.message.reply_text(
        f"ℹ️ *Le tue informazioni:*\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"📱 Username: @{username}\n"
        f"👤 Nome: {first_name}",
        parse_mode="Markdown"
    )

# ---------- MAIN ----------
app = ApplicationBuilder().token(TOKEN).build()

# Comandi principali
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("clear", clear_orders))
app.add_handler(CommandHandler("myid", myid))

# Callback dei bottoni
app.add_handler(CallbackQueryHandler(handle_product, pattern="^prodotto_"))
app.add_handler(CallbackQueryHandler(handle_time, pattern="^time_"))

# Messaggi di testo
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

print("🤖 Bot avviato e pronto! Rimarrà sempre attivo...")
print(f"📋 OWNER_ID configurato: {OWNER_ID}")
print("💡 Assicurati di aver inviato /start al bot almeno una volta!")
app.run_polling()
