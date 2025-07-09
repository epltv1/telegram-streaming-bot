# Telegram Streaming Bot

A Telegram bot to stream M3U8 links to RTMP destinations using FFmpeg.

## Commands
- `/stream <m3u8_url> <rtmp_url> <stream_key>`: Start streaming.
  Example: `/stream http://example.com/playlist.m3u8 rtmp://a.rtmp.youtube.com/live2 abcd-1234-efgh-5678`
- `/list`: List active streams with IDs (e.g., Stream 882828).
- `/stop`: Stop all streams.
- `/stop <stream_id>`: Stop a specific stream.
- `/streamstat`: Show stats for active streams (duration, bitrate).
- `/stat`: Show bot uptime.
- `/help`: Show usage instructions.

## Setup on Deepnote VPS
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/telegram-streaming-bot.git
   cd telegram-streaming-bot
