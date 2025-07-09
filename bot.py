import os
import subprocess
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from dotenv import load_dotenv

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Global variable to track FFmpeg process
ffmpeg_process = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Welcome to the Streaming Bot! Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display help message with command usage."""
    help_text = (
        "/stream <m3u8_url> <rtmp_url> <stream_key> - Stream an M3U8 link to an RTMP destination.\n"
        "Example: /stream http://example.com/playlist.m3u8 rtmp://a.rtmp.youtube.com/live2 abcd-1234-efgh-5678\n"
        "/stop - Stop the current stream.\n"
        "/help - Show this help message."
    )
    await update.message.reply_text(help_text)

async def stream(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start streaming from M3U8 to RTMP."""
    global ffmpeg_process

    # Get the full command text after /stream
    command_text = update.message.text[len("/stream "):].strip()
    args = command_text.split(" ", 2)  # Split into at most 3 parts

    # Log the received arguments for debugging
    logger.info(f"Received arguments: {args}")
    await update.message.reply_text(f"Debug: Received arguments: {args}")

    # Check if arguments are provided
    if len(args) != 3:
        await update.message.reply_text(
            f"Usage: /stream <m3u8_url> <rtmp_url> <stream_key>\n"
            f"Example: /stream http://example.com/playlist.m3u8 rtmp://a.rtmp.youtube.com/live2 abcd-1234-efgh-5678\n"
            f"Received: {args}"
        )
        return

    m3u8_url, rtmp_url, stream_key = args

    # Validate URLs (basic check)
    if not m3u8_url.startswith("http") or not rtmp_url.startswith("rtmp"):
        await update.message.reply_text("Invalid M3U8 or RTMP URL. Please check and try again.")
        return

    # Check if a stream is already running
    if ffmpeg_process and ffmpeg_process.poll() is None:
        await update.message.reply_text("A stream is already running. Use /stop to end it first.")
        return

    # Construct the full RTMP destination
    full_rtmp_url = f"{rtmp_url}/{stream_key}"

    # FFmpeg command to stream M3U8 to RTMP
    ffmpeg_cmd = [
        "ffmpeg",
        "-re",
        "-i", m3u8_url,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "3500k",
        "-maxrate", "3500k",
        "-bufsize", "7000k",
        "-pix_fmt", "yuv420p",
        "-g", "50",
        "-c:a", "aac",
        "-b:a", "160k",
        "-ac", "2",
        "-ar", "44100",
        "-f", "flv",
        full_rtmp_url
    ]

    try:
        # Start FFmpeg process
        ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await update.message.reply_text(f"Started streaming from {m3u8_url} to {full_rtmp_url}")
    except Exception as e:
        await update.message.reply_text(f"Error starting stream: {str(e)}")
        logger.error(f"Error starting stream: {str(e)}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop the current stream."""
    global ffmpeg_process

    if ffmpeg_process and ffmpeg_process.poll() is None:
        ffmpeg_process.terminate()
        try:
            ffmpeg_process.wait(timeout=5)
            await update.message.reply_text("Stream stopped successfully.")
        except subprocess.TimeoutExpired:
            ffmpeg_process.kill()
            await update.message.reply_text("Stream forcefully stopped.")
        ffmpeg_process = None
    else:
        await update.message.reply_text("No stream is currently running.")

def main():
    """Run the bot."""
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found in .env file.")
        return

    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stream", stream))
    application.add_handler(CommandHandler("stop", stop))

    # Start the bot
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
