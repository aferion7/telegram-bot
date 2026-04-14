from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from dotenv import load_dotenv
import os

load_dotenv()  # .env faylni o‘qiydi

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

reply_map = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    ref = None
    if context.args:
        ref = context.args[0]

    # faqat adminga ko'rinadi
    if ref and str(user.id) != ref:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                f"📊 Yangi user referral orqali kirdi!\n\n"
                f"👤 {user.full_name}\n"
                f"🆔 {user.id}\n"
                f"🔗 Taklif qilgan ID: {ref}"
            )
        )

    user_link = f"https://t.me/{context.bot.username}?start={user.id}"

    # userga esa referrer ko'rsatilmaydi
    await update.message.reply_text(
        f"👋 Salom!\n\n"
        f"📩 Anonim xabar yuborishingiz mumkin.\n\n"
        f"🔗 Sizning shaxsiy linkingiz:\n{user_link}\n\n"
        f"🚀 Do'stlaringizga yuboring!"
    )


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        return

    user = update.effective_user
    msg = update.message

    info = (
        f"Kim yubordi:\n"
        f"Ism: {user.full_name}\n"
        f"Username: @{user.username if user.username else 'yoq'}\n"
        f"ID: {user.id}\n\n"
        f"Javob berish uchun shu xabarga reply qiling."
    )

    sent = None

    if msg.text:
        sent = await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"Yangi anonim xabar:\n{msg.text}\n\n{info}"
        )
    elif msg.photo:
        sent = await context.bot.send_photo(
            chat_id=OWNER_ID,
            photo=msg.photo[-1].file_id,
            caption=f"Yangi anonim rasm\n\n{info}"
        )
    elif msg.video:
        sent = await context.bot.send_video(
            chat_id=OWNER_ID,
            video=msg.video.file_id,
            caption=f"Yangi anonim video\n\n{info}"
        )
    elif msg.audio:
        sent = await context.bot.send_audio(
            chat_id=OWNER_ID,
            audio=msg.audio.file_id,
            caption=f"Yangi anonim audio\n\n{info}"
        )
    elif msg.voice:
        sent = await context.bot.send_voice(
            chat_id=OWNER_ID,
            voice=msg.voice.file_id,
            caption=f"Yangi anonim voice xabar\n\n{info}"
        )
    elif msg.document:
        sent = await context.bot.send_document(
            chat_id=OWNER_ID,
            document=msg.document.file_id,
            caption=f"Yangi anonim fayl\n\n{info}"
        )

    if sent:
        reply_map[sent.message_id] = user.id
        print(f"Saved: admin message {sent.message_id} -> user {user.id}")

    await update.message.reply_text("Xabaringiz yuborildi.")


async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not update.message.reply_to_message:
        return

    replied_message_id = update.message.reply_to_message.message_id
    target_user_id = reply_map.get(replied_message_id)

    print(f"Admin replied to message_id: {replied_message_id}")
    print(f"Found target user: {target_user_id}")

    if not target_user_id:
        await update.message.reply_text("Bu xabarga anonim reply qilib bo'lmaydi.")
        return

    reply_note = "\n\nAgar javob bermoqchi bo'lsangiz, shunchaki shu yerga yozing."

    if update.message.text:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"📩 Admin javobi:\n{update.message.text}{reply_note}"
        )
    elif update.message.photo:
        caption = update.message.caption or ""
        await context.bot.send_photo(
            chat_id=target_user_id,
            photo=update.message.photo[-1].file_id,
            caption=f"📩 Admin javobi:\n{caption}{reply_note}"
        )
    elif update.message.video:
        caption = update.message.caption or ""
        await context.bot.send_video(
            chat_id=target_user_id,
            video=update.message.video.file_id,
            caption=f"📩 Admin javobi:\n{caption}{reply_note}"
        )
    elif update.message.audio:
        caption = update.message.caption or ""
        await context.bot.send_audio(
            chat_id=target_user_id,
            audio=update.message.audio.file_id,
            caption=f"📩 Admin javobi:\n{caption}{reply_note}"
        )
    elif update.message.voice:
        await context.bot.send_voice(
            chat_id=target_user_id,
            voice=update.message.voice.file_id
        )
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"Agar javob bermoqchi bo'lsangiz, shunchaki shu yerga yozing."
        )
    elif update.message.document:
        caption = update.message.caption or ""
        await context.bot.send_document(
            chat_id=target_user_id,
            document=update.message.document.file_id,
            caption=f"📩 Admin javobi:\n{caption}{reply_note}"
        )
    else:
        await update.message.reply_text("Faqat matn, rasm, video, audio, voice yoki fayl yuboring.")
        return

    await update.message.reply_text("Javob yuborildi.")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(filters.REPLY & filters.User(user_id=OWNER_ID), handle_admin_reply)
    )

    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE | filters.Document.ALL)
            & ~filters.User(user_id=OWNER_ID),
            handle_user_message,
        )
    )

    print("Bot ishlayapti...")
    app.run_polling()


if __name__ == "__main__":
    main()
