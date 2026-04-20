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

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

if not TOKEN or not OWNER_ID:
    raise ValueError("BOT_TOKEN yoki OWNER_ID topilmadi")

web_app = Flask(__name__)
tg_app = Application.builder().token(TOKEN).build()

# user -> link egasi
user_targets = {}

# admin/user reply tracking
pending_replies = {}

# async loop
bot_loop = asyncio.new_event_loop()
threading.Thread(target=lambda: asyncio.set_event_loop(bot_loop) or bot_loop.run_forever(), daemon=True).start()
def run_async(coro): return asyncio.run_coroutine_threadsafe(coro, bot_loop)

async def setup_bot(): await tg_app.initialize()
run_async(setup_bot()).result()

def make_admin_button(user_id): return InlineKeyboardMarkup([[InlineKeyboardButton("Javob berish ✍️", callback_data=f"admin_reply_{user_id}")]])
def make_user_button(): return InlineKeyboardMarkup([[InlineKeyboardButton("Javob berish ✍️", callback_data="user_reply")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ref = context.args[0] if context.args else None
    if ref and str(user.id) != ref:
        try: user_targets[user.id] = int(ref)
        except: pass
        await context.bot.send_message(chat_id=OWNER_ID, text=f"📊 Yangi user referral:\n{user.full_name}\nID: {user.id}\nLink egasi: {ref}")
    user_link = f"https://t.me/{context.bot.username}?start={user.id}"
    await update.message.reply_text(f"👋 Salom!\nAnonim xabar yuborishingiz mumkin.\n🔗 Sizning shaxsiy linkingiz:\n{user_link}")

async def send_any_message(bot, chat_id, msg, caption, reply_markup=None):
    if msg.text: await bot.send_message(chat_id, f"{caption}\n\n{msg.text}", reply_markup=reply_markup)
    elif msg.photo: await bot.send_photo(chat_id, msg.photo[-1].file_id, caption=f"{caption}\n\n{msg.caption or ''}".strip(), reply_markup=reply_markup)
    elif msg.video: await bot.send_video(chat_id, msg.video.file_id, caption=f"{caption}\n\n{msg.caption or ''}".strip(), reply_markup=reply_markup)
    elif msg.audio: await bot.send_audio(chat_id, msg.audio.file_id, caption=f"{caption}\n\n{msg.caption or ''}".strip(), reply_markup=reply_markup)
    elif msg.voice: await bot.send_voice(chat_id, msg.voice.file_id, caption=caption, reply_markup=reply_markup)
    elif msg.document: await bot.send_document(chat_id, msg.document.file_id, caption=f"{caption}\n\n{msg.caption or ''}".strip(), reply_markup=reply_markup)
    elif msg.sticker: await bot.send_sticker(chat_id, msg.sticker.file_id); 
    if caption: await bot.send_message(chat_id, caption, reply_markup=reply_markup)

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user; msg = update.message
    if user.id == OWNER_ID: return
    target = pending_replies.get(user.id)
    if target == OWNER_ID:
        await send_any_message(context.bot, OWNER_ID, msg, f"📩 User javobi:\n{user.full_name} ({user.id})", make_admin_button(user.id))
        pending_replies.pop(user.id, None)
        await update.message.reply_text("Javob yuborildi.")
        return
    target_user_id = user_targets.get(user.id, OWNER_ID)
    await send_any_message(context.bot, OWNER_ID, msg, f"📩 Yangi anonim xabar\n{user.full_name} ({user.id})", make_admin_button(user.id))
    if target_user_id != OWNER_ID:
        await send_any_message(context.bot, target_user_id, msg, "📩 Sizga anonim xabar keldi.", make_user_button())
    await update.message.reply_text("Xabaringiz yuborildi.")

async def reply_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); user = query.from_user; data = query.data
    if user.id == OWNER_ID and data.startswith("admin_reply_"):
        target_user_id = int(data.split("_")[2]); pending_replies[OWNER_ID] = target_user_id
        await query.message.reply_text("Javob yozing. /cancel yozsangiz bekor qilinadi.")
        return
    if user.id != OWNER_ID and data == "user_reply": pending_replies[user.id] = OWNER_ID; await query.message.reply_text("Javob yozing.")

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    target_user_id = pending_replies.get(OWNER_ID); msg = update.message
    if not target_user_id: return
    if msg.text and msg.text.lower() == "/cancel": pending_replies.pop(OWNER_ID, None); await msg.reply_text("Bekor qilindi."); return
    await send_any_message(context.bot, target_user_id, msg, "📩 Admin javobi:", make_user_button())
    pending_replies.pop(OWNER_ID, None); await msg.reply_text("Javob yuborildi.")

@web_app.route("/"); 
def home(): 
    return "Bot ishlayapti."
@web_app.route("/set_webhook"); 
def set_webhook():
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if not render_url: return "RENDER_EXTERNAL_URL topilmadi."
    webhook_url = f"{render_url}/webhook/{TOKEN}"; result = run_async(tg_app.bot.set_webhook(url=webhook_url)).result(); return f"Webhook o‘rnatildi: {result}"
@web_app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook(): data = request.get_json(force=True); update = Update.de_json(data, tg_app.bot); run_async(tg_app.process_update(update)); return "ok"

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CallbackQueryHandler(reply_button_handler))
tg_app.add_handler(MessageHandler(filters.User(OWNER_ID) & ~filters.COMMAND, handle_admin_message))
tg_app.add_handler(MessageHandler((filters.ALL & ~filters.User(OWNER_ID)), handle_user_message))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000)); web_app.run(host="0.0.0.0", port=port)
