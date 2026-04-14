import os
import asyncio
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

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi")
if not OWNER_ID:
    raise ValueError("OWNER_ID topilmadi")

web_app = Flask(__name__)
tg_app = Application.builder().token(TOKEN).build()

# Kim kimga javob yozayotgani shu yerda saqlanadi
# admin uchun: pending_replies[OWNER_ID] = user_id
# user uchun:  pending_replies[user_id] = OWNER_ID
pending_replies = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    ref = None
    if context.args:
        ref = context.args[0]

    if ref and str(user.id) != ref:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                f"📊 Yangi user referral orqali kirdi!\n\n"
                f"👤 {user.full_name}\n"
                f"🆔 {user.id}\n"
                f"🔗 Taklif qilgan ID: {ref}"
            ),
        )

    user_link = f"https://t.me/{context.bot.username}?start={user.id}"

    await update.message.reply_text(
        f"👋 Salom!\n\n"
        f"📩 Anonim xabar yuborishingiz mumkin.\n\n"
        f"🔗 Sizning shaxsiy linkingiz:\n{user_link}"
    )


def make_admin_reply_button(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Javob berish ✍️", callback_data=f"reply_{user_id}")]]
    )


def make_user_reply_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Javob berish ✍️", callback_data="user_reply")]]
    )


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message

    if user.id == OWNER_ID:
        return

    # Agar user adminning javobiga javob yozayotgan bo‘lsa
    target = pending_replies.get(user.id)
    if target == OWNER_ID:
        info = (
            f"📩 User javobi:\n"
            f"Kim yubordi:\n"
            f"Ism: {user.full_name}\n"
            f"Username: @{user.username if user.username else 'yoq'}\n"
            f"ID: {user.id}"
        )

        keyboard = make_admin_reply_button(user.id)

        if msg.text:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"{info}\n\n{msg.text}",
                reply_markup=keyboard,
            )
        elif msg.photo:
            caption = msg.caption or ""
            await context.bot.send_photo(
                chat_id=OWNER_ID,
                photo=msg.photo[-1].file_id,
                caption=f"{info}\n\n{caption}",
                reply_markup=keyboard,
            )
        elif msg.video:
            caption = msg.caption or ""
            await context.bot.send_video(
                chat_id=OWNER_ID,
                video=msg.video.file_id,
                caption=f"{info}\n\n{caption}",
                reply_markup=keyboard,
            )
        elif msg.audio:
            caption = msg.caption or ""
            await context.bot.send_audio(
                chat_id=OWNER_ID,
                audio=msg.audio.file_id,
                caption=f"{info}\n\n{caption}",
                reply_markup=keyboard,
            )
        elif msg.voice:
            await context.bot.send_voice(
                chat_id=OWNER_ID,
                voice=msg.voice.file_id,
                caption=info,
                reply_markup=keyboard,
            )
        elif msg.document:
            caption = msg.caption or ""
            await context.bot.send_document(
                chat_id=OWNER_ID,
                document=msg.document.file_id,
                caption=f"{info}\n\n{caption}",
                reply_markup=keyboard,
            )
        elif msg.sticker:
            await context.bot.send_sticker(
                chat_id=OWNER_ID,
                sticker=msg.sticker.file_id,
                reply_markup=keyboard,
            )
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=info,
            )
        else:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"Qo‘llab-quvvatlanmaydigan xabar turi.\n\n{info}",
                reply_markup=keyboard,
            )

        pending_replies.pop(user.id, None)
        await update.message.reply_text("Javobingiz yuborildi.")
        return

    # Oddiy anonim xabar
    info = (
        f"Kim yubordi:\n"
        f"Ism: {user.full_name}\n"
        f"Username: @{user.username if user.username else 'yoq'}\n"
        f"ID: {user.id}"
    )

    keyboard = make_admin_reply_button(user.id)

    if msg.text:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"Yangi anonim xabar:\n{msg.text}\n\n{info}",
            reply_markup=keyboard,
        )

    elif msg.photo:
        caption = msg.caption or ""
        await context.bot.send_photo(
            chat_id=OWNER_ID,
            photo=msg.photo[-1].file_id,
            caption=f"Yangi anonim rasm\n\n{caption}\n\n{info}",
            reply_markup=keyboard,
        )

    elif msg.video:
        caption = msg.caption or ""
        await context.bot.send_video(
            chat_id=OWNER_ID,
            video=msg.video.file_id,
            caption=f"Yangi anonim video\n\n{caption}\n\n{info}",
            reply_markup=keyboard,
        )

    elif msg.audio:
        caption = msg.caption or ""
        await context.bot.send_audio(
            chat_id=OWNER_ID,
            audio=msg.audio.file_id,
            caption=f"Yangi anonim audio\n\n{caption}\n\n{info}",
            reply_markup=keyboard,
        )

    elif msg.voice:
        await context.bot.send_voice(
            chat_id=OWNER_ID,
            voice=msg.voice.file_id,
            caption=f"Yangi anonim voice\n\n{info}",
            reply_markup=keyboard,
        )

    elif msg.document:
        caption = msg.caption or ""
        await context.bot.send_document(
            chat_id=OWNER_ID,
            document=msg.document.file_id,
            caption=f"Yangi anonim fayl\n\n{caption}\n\n{info}",
            reply_markup=keyboard,
        )

    elif msg.sticker:
        await context.bot.send_sticker(
            chat_id=OWNER_ID,
            sticker=msg.sticker.file_id,
            reply_markup=keyboard,
        )
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=info,
        )

    else:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"Qo‘llab-quvvatlanmaydigan xabar turi.\n\n{info}",
            reply_markup=keyboard,
        )

    await update.message.reply_text("Xabaringiz yuborildi.")


async def reply_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data

    # Admin tugmasi
    if user.id == OWNER_ID and data.startswith("reply_"):
        target_user_id = int(data.split("_")[1])
        pending_replies[OWNER_ID] = target_user_id
        await query.message.reply_text("Javobingizni yuboring. Bekor qilish uchun /cancel yozing.")
        return

    # User tugmasi
    if user.id != OWNER_ID and data == "user_reply":
        pending_replies[user.id] = OWNER_ID
        await query.message.reply_text("Javobingizni yozing.")
        return


async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    target_user_id = pending_replies.get(OWNER_ID)
    if not target_user_id:
        return

    msg = update.message

    if msg.text and msg.text == "/cancel":
        pending_replies.pop(OWNER_ID, None)
        await update.message.reply_text("Bekor qilindi.")
        return

    note = "\n\nAgar javob bermoqchi bo'lsangiz, shu tugmani bosing."
    keyboard = make_user_reply_button()

    if msg.text:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"📩 Admin javobi:\n{msg.text}{note}",
            reply_markup=keyboard,
        )

    elif msg.photo:
        caption = msg.caption or ""
        await context.bot.send_photo(
            chat_id=target_user_id,
            photo=msg.photo[-1].file_id,
            caption=f"📩 Admin javobi:\n{caption}{note}",
            reply_markup=keyboard,
        )

    elif msg.video:
        caption = msg.caption or ""
        await context.bot.send_video(
            chat_id=target_user_id,
            video=msg.video.file_id,
            caption=f"📩 Admin javobi:\n{caption}{note}",
            reply_markup=keyboard,
        )

    elif msg.audio:
        caption = msg.caption or ""
        await context.bot.send_audio(
            chat_id=target_user_id,
            audio=msg.audio.file_id,
            caption=f"📩 Admin javobi:\n{caption}{note}",
            reply_markup=keyboard,
        )

    elif msg.voice:
        await context.bot.send_voice(
            chat_id=target_user_id,
            voice=msg.voice.file_id,
        )
        await context.bot.send_message(
            chat_id=target_user_id,
            text="Agar javob bermoqchi bo'lsangiz, shu tugmani bosing.",
            reply_markup=keyboard,
        )

    elif msg.document:
        caption = msg.caption or ""
        await context.bot.send_document(
            chat_id=target_user_id,
            document=msg.document.file_id,
            caption=f"📩 Admin javobi:\n{caption}{note}",
            reply_markup=keyboard,
        )

    elif msg.sticker:
        await context.bot.send_sticker(
            chat_id=target_user_id,
            sticker=msg.sticker.file_id,
        )
        await context.bot.send_message(
            chat_id=target_user_id,
            text="Agar javob bermoqchi bo'lsangiz, shu tugmani bosing.",
            reply_markup=keyboard,
        )

    else:
        await update.message.reply_text("Faqat matn, rasm, video, audio, voice, fayl yoki sticker yuboring.")
        return

    pending_replies.pop(OWNER_ID, None)
    await update.message.reply_text("Javob yuborildi.")


@web_app.route("/")
def home():
    return "Bot ishlayapti."


@web_app.route("/set_webhook")
def set_webhook():
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if not render_url:
        return "RENDER_EXTERNAL_URL topilmadi."

    webhook_url = f"{render_url}/webhook/{TOKEN}"
    result = asyncio.run(tg_app.bot.set_webhook(url=webhook_url))
    return f"Webhook o‘rnatildi: {result}"


@web_app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, tg_app.bot)
    asyncio.run(process_update(update))
    return "ok"


async def process_update(update: Update):
    if not getattr(tg_app, "_initialized", False):
        await tg_app.initialize()
        tg_app._initialized = True
    await tg_app.process_update(update)


tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CallbackQueryHandler(reply_button_handler))
tg_app.add_handler(
    MessageHandler(
        filters.User(user_id=OWNER_ID) & ~filters.COMMAND,
        handle_admin_message,
    )
)
tg_app.add_handler(
    MessageHandler(
        (
            filters.TEXT
            | filters.PHOTO
            | filters.VIDEO
            | filters.AUDIO
            | filters.VOICE
            | filters.Document.ALL
            | filters.Sticker.ALL
        ) & ~filters.User(user_id=OWNER_ID),
        handle_user_message,
    )
)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)
