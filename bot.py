import os
import sqlite3
import logging
import requests
import asyncio
from functools import wraps
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import get_connection

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def restricted(func):
    """Decorator to restrict access to allowed user IDs only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = str(update.effective_user.id)
        allowed_users = [u.strip() for u in os.getenv("ALLOWED_USER_IDS", "").split(",") if u.strip()]
        
        if user_id not in allowed_users:
            logger.warning(f"Unauthorized access denied for {user_id}.")
            if update.callback_query:
                await update.callback_query.answer("⛔️ Unauthorized", show_alert=True)
            elif update.message:
                await update.message.reply_text(f"⛔️ Unauthorized access.\n\nYour User ID is `{user_id}`.\n\nPlease add it to the ALLOWED_USER_IDS in the .env file to use this bot.", parse_mode='Markdown')
            return
            
        return await func(update, context, *args, **kwargs)
    return wrapper

def fetch_definition(word):
    try:
        response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data[0]['meanings'][0]['definitions'][0]['definition']
    except Exception as e:
        logger.error(f"Error fetching definition for {word}: {e}")
    return "Definition not available."

def fetch_translation(word):
    try:
        translator = GoogleTranslator(source='en', target='ru')
        return translator.translate(word)
    except Exception as e:
        logger.error(f"Error fetching translation for {word}: {e}")
        return "Translation not available."

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = (
        "👋 Hello! I am your Vocabulary Bot.\n\n"
        "Here are my commands:\n"
        "🔹 /nextbatch - Get a new batch of 10 words to learn.\n"
        "🔹 /batch <id> - View a specific batch.\n"
        "🔹 /review <id> - Review a specific batch.\n"
    )
    await update.message.reply_text(welcome_message)

@restricted
async def nextbatch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Creates a new batch of 10 words and sends them to the user."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get 10 words that are 'new' or 'learning', prioritizing easier levels
    cursor.execute('''
        SELECT id, word, word_type, definition, translation, level
        FROM words 
        WHERE status IN ('new', 'learning') 
        ORDER BY level ASC, RANDOM() 
        LIMIT 10
    ''')
    words_db = cursor.fetchall()

    if not words_db:
        await update.message.reply_text("🎉 You have no more new or learning words in the queue! Add more words to the database.")
        conn.close()
        return

    # Let the user know we are generating it because it might take a few seconds
    status_msg = await update.message.reply_text("⏳ Generating your batch and fetching translations...")

    # Create a new batch
    cursor.execute('INSERT INTO batches DEFAULT VALUES')
    batch_id = cursor.lastrowid

    # Link words to batch and update status to 'learning'
    message_lines = [f"📚 *Batch #{batch_id}*"]
    
    for w_id, word, word_type, definition, translation, level in words_db:
        # Lazy load definition
        if not definition:
            definition = fetch_definition(word)
        
        # Lazy load translation
        if not translation:
            translation = fetch_translation(word)
            
        cursor.execute('''
            UPDATE words SET status = 'learning', definition = ?, translation = ?
            WHERE id = ?
        ''', (definition, translation, w_id))
        
        cursor.execute('INSERT INTO batch_words (batch_id, word_id) VALUES (?, ?)', (batch_id, w_id))
        
        type_str = f" ({word_type})" if word_type else ""
        level_str = f" [{level}]" if level else ""
        message_lines.append(f"\n🇬🇧 *{word}*{type_str}{level_str}\n📖 {definition}\n🇷🇺 {translation}")

    conn.commit()
    conn.close()

    message = "\n".join(message_lines)
    message += f"\n\n*When ready, use* `/review {batch_id}` *to review!*"
    
    await status_msg.delete()
    await update.message.reply_text(message, parse_mode='Markdown')

@restricted
async def view_batch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View words in a specific batch."""
    try:
        batch_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid batch ID. Usage: `/batch 1`", parse_mode='Markdown')
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT w.word, w.word_type, w.definition, w.translation, w.status, w.level
        FROM words w
        JOIN batch_words bw ON w.id = bw.word_id
        WHERE bw.batch_id = ?
    ''', (batch_id,))
    words = cursor.fetchall()
    conn.close()

    if not words:
        await update.message.reply_text(f"❌ Batch #{batch_id} not found.")
        return

    message_lines = [f"📚 *Batch #{batch_id}*"]
    for word, word_type, definition, translation, status, level in words:
        status_emoji = "✅" if status == 'known' else "🔄"
        type_str = f" ({word_type})" if word_type else ""
        level_str = f" [{level}]" if level else ""
        message_lines.append(f"\n{status_emoji} 🇬🇧 *{word}*{type_str}{level_str}\n📖 {definition}\n🇷🇺 {translation}")

    await update.message.reply_text("\n".join(message_lines), parse_mode='Markdown')

@restricted
async def review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start interactive review for a batch."""
    try:
        batch_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid batch ID. Usage: `/review 1`", parse_mode='Markdown')
        return

    # Store batch_id and start index in context
    context.user_data['review_batch_id'] = batch_id
    context.user_data['review_index'] = 0

    await send_next_review_word(update.message, context)

async def send_next_review_word(message_obj, context: ContextTypes.DEFAULT_TYPE) -> None:
    batch_id = context.user_data.get('review_batch_id')
    index = context.user_data.get('review_index', 0)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT w.id, w.word, w.word_type, w.translation, w.level
        FROM words w
        JOIN batch_words bw ON w.id = bw.word_id
        WHERE bw.batch_id = ?
        ORDER BY bw.rowid
    ''', (batch_id,))
    words = cursor.fetchall()
    conn.close()

    if index >= len(words):
        await message_obj.reply_text(f"🎉 You have completed reviewing Batch #{batch_id}!")
        context.user_data.pop('review_batch_id', None)
        context.user_data.pop('review_index', None)
        return

    word_id, word, word_type, translation, level = words[index]
    type_str = f" ({word_type})" if word_type else ""
    level_str = f" [{level}]" if level else ""

    keyboard = [
        [
            InlineKeyboardButton("✅ Known", callback_data=f"known_{word_id}"),
            InlineKeyboardButton("🔄 Repeat", callback_data=f"repeat_{word_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message_obj.reply_text(
        f"Review Word {index + 1}/{len(words)}:\n\n🇬🇧 *{word}*{type_str}{level_str}\n🇷🇺 {translation}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

@restricted
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates message text."""
    query = update.callback_query
    await query.answer()

    data = query.data
    action, word_id = data.split('_')
    word_id = int(word_id)

    conn = get_connection()
    cursor = conn.cursor()

    if action == "known":
        cursor.execute("UPDATE words SET status = 'known' WHERE id = ?", (word_id,))
        result_text = "✅ Marked as Known"
    elif action == "repeat":
        cursor.execute("UPDATE words SET status = 'learning' WHERE id = ?", (word_id,))
        result_text = "🔄 Kept in Queue"

    conn.commit()
    conn.close()

    # Edit the message to show result and remove buttons
    original_text = query.message.text
    await query.edit_message_text(text=f"{original_text}\n\n{result_text}")

    # Send next word
    context.user_data['review_index'] += 1
    await send_next_review_word(query.message, context)


def main() -> None:
    """Start the bot."""
    if not TOKEN or TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error("Please set your TELEGRAM_BOT_TOKEN in the .env file.")
        return

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("nextbatch", nextbatch))
    application.add_handler(CommandHandler("batch", view_batch))
    application.add_handler(CommandHandler("review", review))
    application.add_handler(CallbackQueryHandler(button))

    mode = os.getenv("MODE", "polling").lower()
    
    # Fix for Python 3.14+ Event Loop RuntimeError
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    
    if mode == "webhook":
        port = int(os.getenv("PORT", "8443"))
        webhook_url = os.getenv("WEBHOOK_URL", "").rstrip("/")
        
        if not webhook_url:
            logger.error("WEBHOOK_URL must be set in .env when MODE=webhook")
            return
            
        logger.info(f"Starting bot in Webhook mode on port {port}")
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TOKEN,
            webhook_url=f"{webhook_url}/{TOKEN}"
        )
    else:
        logger.info("Starting bot in Polling mode")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
