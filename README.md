# Telegram Streaming Bot

A Telegram bot to stream M3U8 links to RTMP destinations using FFmpeg.

## Commands
- `/stream <m3u8_url> <rtmp_url> <stream_key>`: Start streaming from an M3U8 URL to an RTMP destination.
  Example: `/stream http://example.com/playlist.m3u8 rtmp://a.rtmp.youtube.com/live2 abcd-1234-efgh-5678`
- `/stop`: Stop the current stream.
- `/help`: Display help with command usage.

## Setup on VPS
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/telegram-streaming-bot.git
   cd telegram-streaming-bot
