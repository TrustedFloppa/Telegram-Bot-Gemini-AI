import logging
import requests
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Read the bot token and Gemini API key from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Google Gemini API endpoint
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-002:generateContent?key={GEMINI_API_KEY}'

# Function to send request to Google Gemini AI
def send_request_to_gemini(user_query):
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": user_query
                    }
                ]
            }
        ]
    }
    
    response = requests.post(GEMINI_API_URL, headers=headers, json=data)
    
    # Log the full response for debugging purposes
    logger.info(f"API Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        # Extract the response text from the correct part of the API result
        try:
            return result['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return f"Unexpected response format received: {response.text}"
    else:
        logger.error(f"Error from Gemini API: {response.status_code}, {response.text}")
        return "Sorry, something went wrong with the AI ​​service."

# Start command
async def start(update: Update, context):
    await update.message.reply_text('Hi! Send me an inquiry and I will ask Google Gemini AI for you.')

# Message handler
async def handle_message(update: Update, context):
    user_message = update.message.text
    # Send an initial processing message
    processing_message = await update.message.reply_text('I am processing your request...')
    
    # Send the user's query to Gemini API and get response
    ai_response = send_request_to_gemini(user_message)
    
    # Edit the processing message with the AI response
    await context.bot.edit_message_text(
        chat_id=update.message.chat_id,
        message_id=processing_message.message_id,
        text=ai_response
    )

# Error handler
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

if __name__ == '__main__':
    # Create Application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Log all errors
    application.add_error_handler(error)

    # Start the Bot
    application.run_polling()
