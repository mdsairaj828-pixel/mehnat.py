import os
import requests
import telebot
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler


# =========================
# Render health-check server
# =========================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Telegram bot is running.")

    def log_message(self, format, *args):
        return


def run_server():
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"Health server running on port {port}")
    server.serve_forever()


Thread(target=run_server, daemon=True).start()


# =========================
# Environment variables
# =========================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("OSINT_API_KEY")

# Your authorized API endpoint
API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "https://l34k-osint.onrender.com/search"
)


if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")

if not API_KEY:
    raise RuntimeError("OSINT_API_KEY is missing")


bot = telebot.TeleBot(BOT_TOKEN)


# =========================
# /start
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "🤖 Bot is active.\n\n"
        "Authorized API query bhejne ke liye message bhejein."
    )


# =========================
# /help
# =========================

@bot.message_handler(commands=["help"])
def help_command(message):
    bot.reply_to(
        message,
        "Commands:\n"
        "/start - Bot start\n"
        "/help - Help\n\n"
        "API lookup ke liye sirf authorized/test data use karein."
    )


# =========================
# API request
# =========================

@bot.message_handler(func=lambda message: True)
def handle_message(message):

    query = (message.text or "").strip()

    if not query:
        return

    status = bot.reply_to(
        message,
        "⏳ API request process ho rahi hai..."
    )

    try:
        params = {
            "key": API_KEY,
            "query": query
        }

        headers = {
            "User-Agent": "TelegramBot/1.0"
        }

        response = requests.get(
            API_BASE_URL,
            params=params,
            headers=headers,
            timeout=25
        )

        print("API status:", response.status_code)

        if response.status_code != 200:
            bot.edit_message_text(
                f"❌ API Error\nHTTP {response.status_code}",
                message.chat.id,
                status.message_id
            )
            return

        # Try JSON first
        try:
            data = response.json()
            result = str(data)
        except ValueError:
            result = response.text

        # Telegram message limit protection
        if len(result) > 3500:
            result = result[:3500] + "\n\n...[output truncated]"

        bot.edit_message_text(
            "✅ API Response:\n\n" + result,
            message.chat.id,
            status.message_id
        )

    except requests.exceptions.Timeout:
        bot.edit_message_text(
            "⏱️ API timeout. Server ne time par response nahi diya.",
            message.chat.id,
            status.message_id
        )

    except requests.exceptions.RequestException as e:
        print("Request error:", e)

        bot.edit_message_text(
            "❌ API connection error.",
            message.chat.id,
            status.message_id
        )

    except Exception as e:
        print("Bot error:", e)

        bot.edit_message_text(
            "❌ Unexpected error.",
            message.chat.id,
            status.message_id
        )


# =========================
# Start bot
# =========================

if __name__ == "__main__":
    print("🚀 Telegram bot starting...")
    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=5
    )        except:
            pass

if __name__ == '__main__':
    print("🚀 Bot restarted successfully with URL optimization...")
    bot.infinity_polling(timeout=60, long_polling_timeout=5)
