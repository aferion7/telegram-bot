import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# kim kimga yozayotganini saqlaydi
user_targets = {}
# admin reply uchun
pending_replies = {}


# 🔹 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    ref = None
    if context.args:
        ref = context.args[0]

    # referral orqali kirsa
    if ref and str(user.id) != ref:
        try:
            user_targets[user.id] = int(ref)
        except:
            pass

    link = f"https://t.me/{context.bot.username}?start={user.id}"

    await update.message.reply_text(
        f"👋 Salom!\n\n"
        f"📩 Anonim xabar yuborishingiz mumkin.\n\n"
        f"🔗 Sizning shaxsiy linkingiz:\n{link}"
    )


# 🔹 USER XABARI
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message

    # kimga yuboriladi
    target_user_id = user_targets.get(user.id, OWNER_ID)

    # tugma
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✍️ Javob berish", callback_data=f"reply_{user.id}")]
    ])

    caption = (
        f"📩 Yangi anonim xabar\n\n"
        f"👤 ID: {user.id}\n"
        f"👤 Name: {user.full_name}"
    )

    # OWNER ga yuborish
    await send_any_message(context, OWNER_ID, msg, caption, keyboard)

    # LINK EGASIGA yuborish (agar OWNER emas bo‘lsa)
    if target_user_id != OWNER_ID:
        await send_any_message(context, target_user_id, msg, "📩 Sizga anonim xabar keldi", keyboard)


# 🔹 ADMIN REPLY BOSILDI
async def reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])
    pending_replies[OWNER_ID] = user_id

    await query.message.reply_text("✍️ Javobni yozing...")


# 🔹 ADMIN JAVOB YOZADI
async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != OWNER_ID:
        return

    target = pending_replies.get(OWNER_ID)
    if not target:
        return

    msg = update.message

    # userga yuboriladi
    await send_any_message(context, target, msg, "📩 Sizga javob keldi")

    # userda ham reply tugma chiqadi
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✍️ Javob berish", callback_data=f"reply_{OWNER_ID}")]
    ])

    await send_any_message(context, target, msg, "📩 Sizga javob keldi", keyboard)

    pending_replies.pop(OWNER_ID, None)


# 🔹 UNIVERSAL SEND (text, photo, video, sticker hammasi)
async def send_any_message(context, chat_id, msg, text, keyboard=None):
    if msg.text:
        await context.bot.send_message(chat_id, f"{text}\n\n{msg.text}", reply_markup=keyboard)

    elif msg.photo:
        await context.bot.send_photo(chat_id, msg.photo[-1].file_id, caption=text, reply_markup=keyboard)

    elif msg.video:
        await context.bot.send_video(chat_id, msg.video.file_id, caption=text, reply_markup=keyboard)

    elif msg.sticker:
        await context.bot.send_sticker(chat_id, msg.sticker.file_id)

    else:
        await context.bot.send_message(chat_id, text)


# 🔹 MAIN
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(reply_button, pattern="^reply_"))

    # admin message
    app.add_handler(MessageHandler(filters.ALL & filters.User(OWNER_ID), handle_admin_message))

    # oddiy user message
    app.add_handler(MessageHandler(filters.ALL & ~filters.User(OWNER_ID), handle_user_message))

    app.run_polling()


if __name__ == "__main__":
    main()
