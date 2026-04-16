import os
import asyncio
import threading
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ===== LOAD ENV =====
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

if not TOKEN or not OWNER_ID:
    raise ValueError("BOT_TOKEN yoki OWNER_ID topilmadi")

web_app = Flask(__name__)
tg_app = Application.builder().token(TOKEN).build()

# ===== GLOBAL VAR =====
pending_replies = {}  # kimga javob yozish kerak

# ===== ASYNC LOOP =====
bot_loop = asyncio.new_event_loop()
def start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()
threading.Thread(target=start_background_loop, args=(bot_loop,), daemon=True).start()
def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, bot_loop)
async def setup_bot():
    await tg_app.initialize()
run_async(setup_bot()).result()

# ===== BUTTONS =====
def make_admin_button(user_id:int):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Javob berish ✍️", callback_data=f"reply_{user_id}")]])
def make_user_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Javob berish ✍️", callback_data="user_reply")]])

# ===== START =====
async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ref = None
    if context.args:
        ref = context.args[0]
    if ref and str(user.id)!=ref:
        await context.bot.send_message(chat_id=OWNER_ID,
            text=f"📊 Referral:\n{user.full_name}\nID: {user.id}\nTaklif qilgan ID: {ref}")
    user_link = f"https://t.me/{context.bot.username}?start={user.id}"
    await update.message.reply_text(f"👋 Salom!\nAnonim xabar yuborishingiz mumkin.\n🔗 Sizning linkingiz:\n{user_link}")

# ===== HANDLE USER MESSAGE =====
async def handle_user_message(update:Update, context:ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    # Agar user admin javobiga javob yozsa
    target = pending_replies.get(user.id)
    if target == OWNER_ID:
        keyboard = make_admin_button(user.id)
        info = f"📩 User javobi:\nIsm: {user.full_name}\nUsername: @{user.username if user.username else 'yoq'}\nID: {user.id}"
        if msg.text: await context.bot.send_message(chat_id=OWNER_ID, text=f"{info}\n\n{msg.text}", reply_markup=keyboard)
        elif msg.photo: await context.bot.send_photo(chat_id=OWNER_ID, photo=msg.photo[-1].file_id, caption=f"{info}\n\n{msg.caption or ''}", reply_markup=keyboard)
        elif msg.video: await context.bot.send_video(chat_id=OWNER_ID, video=msg.video.file_id, caption=f"{info}\n\n{msg.caption or ''}", reply_markup=keyboard)
        elif msg.audio: await context.bot.send_audio(chat_id=OWNER_ID, audio=msg.audio.file_id, caption=f"{info}\n\n{msg.caption or ''}", reply_markup=keyboard)
        elif msg.voice: await context.bot.send_voice(chat_id=OWNER_ID, voice=msg.voice.file_id, caption=info, reply_markup=keyboard)
        elif msg.document: await context.bot.send_document(chat_id=OWNER_ID, document=msg.document.file_id, caption=f"{info}\n\n{msg.caption or ''}", reply_markup=keyboard)
        elif msg.sticker: await context.bot.send_sticker(chat_id=OWNER_ID, sticker=msg.sticker.file_id, reply_markup=keyboard); await context.bot.send_message(chat_id=OWNER_ID,text=info)
        pending_replies.pop(user.id,None)
        await update.message.reply_text("Javob yuborildi")
        return

    # oddiy anonim xabar
    keyboard = make_admin_button(user.id)
    target_user_id = OWNER_ID if not context.args else int(context.args[0])
    info = f"Ism: {user.full_name}\nUsername: @{user.username if user.username else 'yoq'}\nID: {user.id}"
    # admin ga yuborish
    if msg.text: await context.bot.send_message(chat_id=OWNER_ID,text=f"📩 Anonim xabar:\n{msg.text}\n\n{info}",reply_markup=keyboard)
    elif msg.photo: await context.bot.send_photo(chat_id=OWNER_ID, photo=msg.photo[-1].file_id, caption=f"📩 Anonim rasm\n\n{msg.caption or ''}\n\n{info}", reply_markup=keyboard)
    elif msg.video: await context.bot.send_video(chat_id=OWNER_ID, video=msg.video.file_id, caption=f"📩 Anonim video\n\n{msg.caption or ''}\n\n{info}", reply_markup=keyboard)
    elif msg.audio: await context.bot.send_audio(chat_id=OWNER_ID, audio=msg.audio.file_id, caption=f"📩 Anonim audio\n\n{msg.caption or ''}\n\n{info}", reply_markup=keyboard)
    elif msg.voice: await context.bot.send_voice(chat_id=OWNER_ID, voice=msg.voice.file_id, caption=f"📩 Anonim voice\n\n{info}", reply_markup=keyboard)
    elif msg.document: await context.bot.send_document(chat_id=OWNER_ID, document=msg.document.file_id, caption=f"📩 Anonim fayl\n\n{msg.caption or ''}\n\n{info}", reply_markup=keyboard)
    elif msg.sticker: await context.bot.send_sticker(chat_id=OWNER_ID, sticker=msg.sticker.file_id, reply_markup=keyboard); await context.bot.send_message(chat_id=OWNER_ID,text=info)

    # userga yuborish (anonim)
    if msg.text: await context.bot.send_message(chat_id=target_user_id,text=f"📩 Sizga anonim xabar:\n\n{msg.text}")
    elif msg.photo: await context.bot.send_photo(chat_id=target_user_id, photo=msg.photo[-1].file_id, caption="📩 Sizga anonim rasm")
    elif msg.video: await context.bot.send_video(chat_id=target_user_id, video=msg.video.file_id, caption="📩 Sizga anonim video")
    elif msg.sticker: await context.bot.send_sticker(chat_id=target_user_id, sticker=msg.sticker.file_id)
    await update.message.reply_text("Xabaringiz yuborildi.")

# ===== BUTTON HANDLER =====
async def reply_button_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data
    if user.id == OWNER_ID and data.startswith("reply_"):
        target_user_id = int(data.split("_")[1])
        pending_replies[OWNER_ID] = target_user_id
        await query.message.reply_text("Javobingizni yuboring. /cancel yozsangiz bekor qilinadi.")
        return
    if user.id != OWNER_ID and data=="user_reply":
        pending_replies[user.id] = OWNER_ID
        await query.message.reply_text("Javobingizni yozing.")

# ===== ADMIN MESSAGE =====
async def handle_admin_message(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    target_user_id = pending_replies.get(OWNER_ID)
    if not target_user_id: return
    msg = update.message
    if msg.text=="/cancel":
        pending_replies.pop(OWNER_ID,None)
        await update.message.reply_text("Bekor qilindi")
        return
    note = "\n\nAgar javob bermoqchi bo'lsangiz, tugmani bosing."
    keyboard = make_user_button()
    if msg.text: await context.bot.send_message(chat_id=target_user_id,text=f"📩 Admin javobi:\n{msg.text}{note}",reply_markup=keyboard)
    elif msg.photo: await context.bot.send_photo(chat_id=target_user_id, photo=msg.photo[-1].file_id, caption=f"📩 Admin javobi:\n{msg.caption or ''}{note}", reply_markup=keyboard)
    elif msg.video: await context.bot.send_video(chat_id=target_user_id, video=msg.video.file_id, caption=f"📩 Admin javobi:\n{msg.caption or ''}{note}", reply_markup=keyboard)
    elif msg.audio: await context.bot.send_audio(chat_id=target_user_id, audio=msg.audio.file_id, caption=f"📩 Admin javobi:\n{msg.caption or ''}{note}", reply_markup=keyboard)
    elif msg.voice: await context.bot.send_voice(chat_id=target_user_id, voice=msg.voice.file_id); await context.bot.send_message(chat_id=target_user_id,text=f"Agar javob bermoqchi bo'lsangiz, tugmani bosing", reply_markup=keyboard)
    elif msg.document: await context.bot.send_document(chat_id=target_user_id, document=msg.document.file_id, caption=f"📩 Admin javobi:\n{msg.caption or ''}{note}", reply_markup=keyboard)
    elif msg.sticker: await context.bot.send_sticker(chat_id=target_user_id, sticker=msg.sticker.file_id); await context.bot.send_message(chat_id=target_user_id,text=f"Agar javob bermoqchi bo'lsangiz, tugmani bosing", reply_markup=keyboard)
    pending_replies.pop(OWNER_ID,None)
    await update.message.reply_text("Javob yuborildi.")

# ===== FLASK =====
@web_app.route("/")
def home(): return "Bot ishlayapti."
@web_app.route("/set_webhook")
def set_webhook():
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if not render_url: return "RENDER_EXTERNAL_URL topilmadi."
    webhook_url = f"{render_url}/webhook/{TOKEN}"
    result = run_async(tg_app.bot.set_webhook(url=webhook_url)).result()
    return f"Webhook o‘rnatildi: {result}"
@web_app.route(f"/webhook/{TOKEN}",methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, tg_app.bot)
    run_async(tg_app.process_update(update))
    return "ok"

# ===== HANDLERS =====
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CallbackQueryHandler(reply_button_handler))
tg_app.add_handler(MessageHandler(filters.User(user_id=OWNER_ID) & ~filters.COMMAND, handle_admin_message))
tg_app.add_handler(MessageHandler(
    (filters.TEXT|filters.PHOTO|filters.VIDEO|filters.AUDIO|filters.VOICE|filters.Document.ALL|filters.Sticker.ALL) & ~filters.User(user_id=OWNER_ID),
    handle_user_message
))

if __name__=="__main__":
    port = int(os.getenv("PORT",10000))
    web_app.run(host="0.0.0.0", port=port)
