import telebot
import requests
import json
import os

# Token aur API details env variables se lenge (Security ke liye)
BOT_TOKEN = os.getenv("BOT_TOKEN", "7814000155:AAFS51lMQpoqDaBA0quslHcBk_fF5eHhKS4")
API_KEY = os.getenv("API_KEY", "0c1e5e85d561de4b9373361fbe6557ba")
API_BASE_URL = "https://onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 OSINT Search Bot Ready! Mujhe koi bhi query ya number bhejiye.")

@bot.message_handler(func=lambda message: True)
def handle_osint_search(message):
    query = message.text.strip()
    status_message = bot.reply_to(message, "🔍 Searching...")
    
    try:
        response = requests.get(API_BASE_URL, params={'key': API_KEY, 'query': query})
        if response.status_code == 200:
            data = response.json()
            formatted_data = json.dumps(data, indent=2, ensure_ascii=False)
            
            if len(formatted_data) > 4000:
                with open("result.txt", "w", encoding="utf-8") as f:
                    f.write(formatted_data)
                with open("result.txt", "rb") as f:
                    bot.send_document(message.chat.id, f, caption="📄 Result size big.")
                bot.delete_message(message.chat.id, status_message.message_id)
            else:
                bot.edit_message_text(f"```json\n{formatted_data}\n```", message.chat.id, status_message.message_id, parse_mode='Markdown')
        else:
            bot.edit_message_text(f"❌ Error: {response.status_code}", message.chat.id, status_message.message_id)
    except Exception as e:
        bot.edit_message_text(f"⚠️ Error: {str(e)}", message.chat.id, status_message.message_id)

if __name__ == "__main__":
    bot.infinity_polling()
