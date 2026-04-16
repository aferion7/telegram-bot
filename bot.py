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

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi")
if not OWNER_ID:
    raise ValueError("OWNER_ID topilmadi")

web_app = Flask(__name__)
tg_app = Application.builder().token(TOKEN).build()

# Kim qaysi link orqali kirganini saqlaydi: sender_id -> link_owner_id
user_targets = {}

# Kim kimga reply yozayotganini saqlaydi
# admin uchun: pending_replies[OWNER_ID] = user_id
# user uchun:  pending_replies[user_id] = OWNER_ID
pending_replies = {}

# Bitta umumiy async loop
bot_loop = asyncio.new_event_loop()


def start_background_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


threading.Thread(target=start_background_loop, args=(bot_loop,), daemon=True).start()


def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, bot_loop)


async def setup_bot():
    await tg_app.initialize()


run_async(setup_bot()).result()


def make_admin_reply_button(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Javob berish ✍️", callback_data=f"admin_reply_{user_id}")]]
    )


def make_user_reply_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Javob berish ✍️", callback_data="user_reply")]]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    ref = None
    if context.args:
        ref = context.args[0]

    # Agar boshqa odamning linki orqali kirgan bo'lsa, eslab qolamiz
    if ref and str(user.id) != ref:
        try:
            user_targets[user.id] = int(ref)
        except ValueError:
            pass

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


async def send_message_with_media(bot, chat_id: int, msg, caption_text: str, reply_markup=None):
    if msg.text:
        await bot.send_message(
            chat_id=chat_id,
            text=f"{caption_text}\n\n{msg.text}",
            reply_markup=reply_markup,
        )

    elif msg.photo:
        await bot.send_photo(
            chat_id=chat_id,
            photo=msg.photo[-1].file_id,
            caption=f"{caption_text}\n\n{msg.caption or ''}".strip(),
            reply_markup=reply_markup,
        )

    elif msg.video:
        await bot.send_video(
            chat_id=chat_id,
            video=msg.video.file_id,
            caption=f"{caption_text}\n\n{msg.caption or ''}".strip(),
            reply_markup=reply_markup,
        )

    elif msg.audio:
        await bot.send_audio(
            chat_id=chat_id,
            audio=msg.audio.file_id,
            caption=f"{caption_text}\n\n{msg.caption or ''}".strip(),
            reply_markup=reply_markup,
        )

    elif msg.voice:
        await bot.send_voice(
            chat_id=chat_id,
            voice=msg.voice.file_id,
            caption=caption_text,
            reply_markup=reply_markup,
        )

    elif msg.document:
        await bot.send_document(
            chat_id=chat_id,
            document=msg.document.file_id,
            caption=f"{caption_text}\n\n{msg.caption or ''}".strip(),
            reply_markup=reply_markup,
        )

    elif msg.sticker:
        await bot.send_sticker(
            chat_id=chat_id,
            sticker=msg.sticker.file_id,
        )
        if caption_text:
            await bot.send_message(
                chat_id=chat_id,
                text=caption_text,
                reply_markup=reply_markup,
            )

    else:
        await bot.send_message(
            chat_id=chat_id,
            text=caption_text or "Qo‘llab-quvvatlanmaydigan xabar turi.",
            reply_markup=reply_markup,
        )


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message

    if user.id == OWNER_ID:
        return

    # Agar user admin javobiga javob yozayotgan bo'lsa
    target = pending_replies.get(user.id)
    if target == OWNER_ID:
        info_for_admin = (
            f"📩 User javobi:\n\n"
            f"Kim yubordi:\n"
            f"Ism: {user.full_name}\n"
            f"Username: @{user.username if user.username else 'yoq'}\n"
            f"ID: {user.id}"
        )

        keyboard_for_admin = make_admin_reply_button(user.id)

        await send_message_with_media(
            context.bot,
            OWNER_ID,
            msg,
            info_for_admin,
            keyboard_for_admin,
        )

        pending_replies.pop(user.id, None)
        await update.message.reply_text("Javobingiz yuborildi.")
        return

    # Oddiy anonim xabar
    target_user_id = user_targets.get(user.id, OWNER_ID)

    info_for_admin = (
        f"📩 Yangi anonim xabar\n\n"
        f"Kim yubordi:\n"
        f"Ism: {user.full_name}\n"
        f"Username: @{user.username if user.username else 'yoq'}\n"
        f"ID: {user.id}\n\n"
        f"Qaysi link egasiga boradi: {target_user_id}"
    )

    keyboard_for_admin = make_admin_reply_button(user.id)

    # Adminga yuborish
    await send_message_with_media(
        context.bot,
        OWNER_ID,
        msg,
        info_for_admin,
        keyboard_for_admin,
    )

    # Agar link egasi admin bo'lmasa, o'sha userga anonim yuborish
    if target_user_id != OWNER_ID:
        keyboard_for_user = make_user_reply_button()

        await send_message_with_media(
            context.bot,
            target_user_id,
            msg,
            "📩 Sizga anonim xabar keldi.",
            keyboard_for_user,
        )

    await update.message.reply_text("Xabaringiz yuborildi.")


async def reply_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data

    # Admin reply bosdi
    if user.id == OWNER_ID and data.startswith("admin_reply_"):
        target_user_id = int(data.split("_")[2])
        pending_replies[OWNER_ID] = target_user_id
        await query.message.reply_text("Javobingizni yuboring. Bekor qilish uchun /cancel yozing.")
        return

    # User reply bosdi
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

    keyboard_for_user = make_user_reply_button()

    await send_message_with_media(
        context.bot,
        target_user_id,
        msg,
        "📩 Admin javobi:",
        keyboard_for_user,
    )

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
    result = run_async(tg_app.bot.set_webhook(url=webhook_url)).result()
    return f"Webhook o‘rnatildi: {result}"


@web_app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, tg_app.bot)
    run_async(tg_app.process_update(update))
    return "ok"


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
