import os
import subprocess
import logging
import time
import uuid
from datetime import datetime, timedelta
from telegram import Update, InputFile
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

# Store streams: {stream_id: {"process": subprocess, "m3u8_url": str, "rtmp_url": str, "start_time": datetime, "bitrate": str}}
active_streams = {}
bot_start_time = datetime.now()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message with an image."""
    image_url = "https://i.postimg.cc/9Q9dW4c5/image.jpg"  # Replace with your welcome image
    await update.message.reply_photo(
        photo=image_url,
        caption="Welcome to the Streaming Bot! Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display help message with an image."""
    image_url = "https://i.postimg.cc/9Q9dW4c5/image.jpg"  # Replace with your help image
    help_text = (
        "/stream <m3u8_url> <rtmp_url> <stream_key> - Start streaming (e.g., /stream http://example.com/playlist.m3u8 rtmp://a.rtmp.youtube.com/live2 abcd-1234-efgh-5678)\n"
        "/list - List all active streams with IDs\n"
        "/stop - Stop all streams\n"
        "/stop <stream_id> - Stop a specific stream\n"
        "/streamstat - Show stats for active streams\n"
        "/stat - Show bot uptime\n"
        "/help - Show this help message"
    )
    await update.message.reply_photo(photo=image_url, caption=help_text)

async def stream(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start streaming from M3U8 to RTMP with reconnection logic."""
    global active_streams
    command_text = update.message.text[len("/stream "):].strip()
    args = command_text.split(" ", 2)

    if len(args) != 3:
        image_url = "https://i.postimg.cc/9Q9dW4c5/image.jpg"  # Replace with your error image
        await update.message.reply_photo(
            photo=image_url,
            caption=f"Usage: /stream <m3u8_url> <rtmp_url> <stream_key>\n"
                    f"Example: /stream http://example.com/playlist.m3u8 rtmp://a.rtmp.youtube.com/live2 abcd-1234-efgh-5678\n"
                    f"Received: {args}"
        )
        return

    m3u8_url, rtmp_url, stream_key = args
    if not m3u8_url.startswith("http") or not rtmp_url.startswith("rtmp"):
        image_url = "https://i.postimg.cc/9Q9dW4c5/image.jpg"
        await update.message.reply_photo(photo=image_url, caption="Invalid M3U8 or RTMP URL.")
        return

    # Generate unique stream ID
    stream_id = str(uuid.uuid4())[:6]
    full_rtmp_url = f"{rtmp_url}/{stream_key}"

    # FFmpeg command with reconnection and logging
    ffmpeg_cmd = [
        "ffmpeg",
        "-re",
        "-i", m3u8_url,
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "2000k",
        "-maxrate", "2000k",
        "-bufsize", "4000k",
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
        # Start FFmpeg with logging
        log_file = f"ffmpeg_log_{stream_id}.txt"
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=open(log_file, "a"),
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        # Store stream details
        active_streams[stream_id] = {
            "process": process,
            "m3u8_url": m3u8_url,
            "rtmp_url": full_rtmp_url,
            "start_time": datetime.now(),
            "bitrate": "2000k"
        }
        image_url = "https://i.postimg.cc/9Q9dW4c5/image.jpg"  # Replace with your stream image
        await update.message.reply_photo(
            photo=image_url,
            caption=f"Started stream {stream_id} from {m3u8_url} to {full_rtmp_url}"
        )
    except Exception as e:
        image_url = "https://i.postimg.cc/9Q9dW4c5/image.jpg"
        await update.message.reply_photo(
            photo=image_url,
            caption=f"Error starting stream: {str(e)}"
        )
        logger.error(f"Error starting stream {stream_id}: {str(e)}")

async def list_streams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all active streams with IDs."""
    image_url = "https://i.postimg.cc/9Q9dW4c5/image.jpg"  # Replace with your list image
    if not active_streams:
        await update.message.reply_photo(photo=image_url, caption="No active streams.")
        return
    stream_list = "\n".join(
        f"Stream {sid}: {details['m3u8_url']} -> {details['rtmp_url']}"
        for sid, details in active_streams.items()
    )
    await update.message.reply_photo(
        photo=image_url,
        caption=f"Active streams:\n{stream_list}"
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop all streams or a specific stream by ID."""
    global active_streams
    image_url = "https://i.postimg.cc/9Q9dW4c5/image.jpg"  # Replace with your stop image
    args = update.message.text.split()
    if len(args) == 1:
        # Stop all streams
        for stream_id, details in list(active_streams.items()):
            process = details["process"]
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                    await update.message.reply_photo(
                        photo=image_url,
                        caption=f"Stream {stream_id} stopped."
                    )
                except subprocess.TimeoutExpired:
                    process.kill()
                    await update.message.reply_photo(
                        photo=image_url,
                        caption=f"Stream {stream_id} forcefully stopped."
                    )
            del active_streams[stream_id]
        await update.message.reply_photo(
            photo=image_url,
            caption="All streams stopped." if active_streams else "No streams were running."
        )
    else:
        # Stop specific stream
        stream_id = args[1]
        if stream_id not in active_streams:
            await update.message.reply_photo(
                photo=image_url,
                caption=f"Stream {stream_id} not found."
            )
            return
        process = active_streams[stream_id]["process"]
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
                await update.message.reply_photo(
                    photo=image_url,
                    caption=f"Stream {stream_id} stopped."
                )
            except subprocess.TimeoutExpired:
                process.kill()
                await update.message.reply_photo(
                    photo=image_url,
                    caption=f"Stream {stream_id} forcefully stopped."
                )
        del active_streams[stream_id]

async def stream_stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show stats for active streams."""
    image_url = "https://i.postimg.cc/9Q9dW4c5/image.jpg"  # Replace with your stats image
    if not active_streams:
        await update.message.reply_photo(photo=image_url, caption="No active streams.")
        return
    stats = []
    for sid, details in active_streams.items():
        duration = datetime.now() - details["start_time"]
        duration_str = str(timedelta(seconds=int(duration.total_seconds())))
        stats.append(
            f"Stream {sid}:\n"
            f"  Source: {details['m3u8_url']}\n"
            f"  Destination: {details['rtmp_url']}\n"
            f"  Duration: {duration_str}\n"
            f"  Bitrate: {details['bitrate']}"
        )
    await update.message.reply_photo(
        photo=image_url,
        caption="Stream Stats:\n" + "\n\n".join(stats)
    )

async def stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot uptime."""
    image_url = "https://i.postimg.cc/9Q9dW4c5/image.jpg"  # Replace with your uptime image
    uptime = datetime.now() - bot_start_time
    uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))
    await update.message.reply_photo(
        photo=image_url,
        caption=f"Bot has been running for {uptime_str}."
    )

def main():
    """Run the bot."""
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found in .env file.")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stream", stream))
    application.add_handler(CommandHandler("list", list_streams))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("streamstat", stream_stat))
    application.add_handler(CommandHandler("stat", stat))

    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
