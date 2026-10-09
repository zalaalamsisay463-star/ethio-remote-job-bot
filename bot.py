import os
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
import google.generativeai as genai

# Logging ማዘጋጀት
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# ቁልፎች
BOT_TOKEN = "8640220728:AAH0-c-8mCclYsqinupY8ZpsZ8JxjdYXtHk"
GEMINI_API_KEY = "AQ.Ab8RN6K1XNjabBROtMZCaDhpwS6SDmqZ8cw39cesRLymeHnIwg"  # ያንተን ሙሉ የGemini API Key እዚህ አስገባ
ADMIN_CHAT_ID = "8613322776"

# Gemini ማዋቀር
try:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    logging.error(f"AI config error: {e}")
    ai_model = None

# Render እንዳይዘጋው የሚያደርግ Dummy Server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# የውይይት ደረጃዎች
NAME, PHONE, ADDRESS, STATUS = range(4)

# የመጽሐፉ ሙሉ የእውቀት ማዕከል
SYSTEM_PROMPT = """
አንተ 'Ethio Remote job' የተባልክ የቴሌግራም ቦት ረዳት ነህ።
ስራህ ስለ ቀጥተኛ ሽያጭ (Direct Selling / Network Marketing) እና ስለ 'አልፋ' (ALFA) አለም አቀፍ ድርጅት የተዘጋጀውን መረጃ መሰረት በማድረግ የተጠቃሚዎችን ማንኛውንም ጥያቄ በትህትና፣ በሙያዊ ብቃት እና በአማርኛ ማብራራት ነው።

መሰረታዊ መረጃዎች፦
1. ድርጅቱ፦ አልፋ (ALFA) ዋና ቢሮው አሜሪካ ሲሆን የመጀመሪያው የአፍሪካ ቅርንጫፉ በኢትዮጵያ ተከፍቷል። ወደ ሱዳን፣ ኬንያ፣ ሶማሊያ፣ እስራኤል፣ አንጎላ እና ኡጋንዳ ለመስፋፋት አቅዷል።
2. የግብይት ልዩነት፦ ባህላዊ ግብይት (አምራች -> ጅምላ -> ችርቻሮ -> ተጠቃሚ) በብዙ ደላሎችና ማስታወቂያ ከፍተኛ ወጪ ሲኖረው፤ ቀጥተኛ ሽያጭ (Direct Selling) ምርት ከአምራች በቀጥታ ወደ ተጠቃሚ ይደርሳል፣ ተጠቃሚዎችና አባላት በቃላት ማስታወቂያ ከፍተኛ ኮሚሽን ያገኛሉ።
3. የአባልነት ፓኬጆች፦
   - የሎው (Yellow)፦ $110 (11% ዙር ኮሚሽን፣ ሳምንታዊ ጣሪያ $1,000)
   - ኦሬንጅ (Orange)፦ $210 (12% ዙር ኮሚሽን፣ ሳምንታዊ ጣሪያ $2,000)
   - ግሪን (Green)፦ $410 (14% ዙር ኮሚሽን፣ ሳምንታዊ ጣሪያ $4,000)
   - ጎልደን (Golden)፦ $810 (15% ዙር ኮሚሽን፣ ሳምንታዊ ጣሪያ $5,000)
4. የዙር (Cycle) እና ጉርሻ አሰራር፦ በግራ 600 ነጥብ፣ በቀኝ 600 ነጥብ ሲመጣጠን 1 ዙር (Cycle) ይሆናል። ቀጥተኛ የማስታወቂያ ጉርሻ ከ 16% እስከ 19% ይሰጣል።
5. የደረጃ እድገቶችና ማበረታቻዎች፦
   - CT -> MT -> TT
   - NTB፦ $5,000 ቢሮ ድጎማ ወይም የውጭ ሀገር ጉዞ
   - IBB፦ $10,000 ቢሮ ድጎማ + $15,000 የመኪና ሽልማት
   - GEB፦ $20,000 ቢሮ ድጎማ + $25,000 የመኪና ሽልማት
   - CA፦ $50,000 ቢሮ ድጎማ + $100,000 ዶላር የገንዘብ ሽልማት
   - AL (Alpha Legend)፦ $100,000 ቢሮ ድጎማ + $500,000 ዶላር የህይወት ዘመን ሽልማት
6. ምርቶች፦ ጥራት ያላቸው የጤና መጠበቂያዎች፣ ኮስሞቲክስ፣ አዳዲስ የቴክኖሎጂ ውጤቶች (ለምሳሌ የአየር ላይ ግሎብ)፣ እንዲሁም የአእምሮ እና የአመራር ስልጠናዎች።
7. የመተግበሪያ አገልግሎት፦ ሲ.ኤፍ.ኤስ (CFS App) በ Google Play Store የሚገኝ ሲሆን የደንበኞች አገልግሎትና የቅሬታ መፍቻ መድረክ ነው።
8. የስኬት ስልቶች፦ እጩዎችን ማጨት (Prospecting)፣ 8ቱ የግብዣ ሂደቶች (ፍጥነት፣ ማድነቅ፣ መጋበዝ፣ "እንዲህ ባደርግልህ... ታደርጋለህ?" ጥያቄ፣ የጊዜ ቁርጠኝነት መውሰድ፣ ስልክ መዝጋት) እና ተቃውሞዎችን በአግባቡ ማስተናገድ።

ደንበኞች ስለስራው፣ ስለ ክፍያው፣ ስለ ፓኬጆች ወይም ስለ ድርጅቱ ህጋዊነት ሲጠይቁ ከዚህ መረጃ በመነሳት አሳማኝ፣ አበረታች፣ ግልጽ እና ማራኪ በሆነ አማርኛ መልስ ስጥ።
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "እንኳን ወደ *Ethio Remote job* በሰላም መጡ! 🌟\n\n"
        "ለመጀመር እባክዎ ሙሉ ስምዎን (Full Name) ይጻፉልን፡",
        parse_mode="Markdown",
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text
    await update.message.reply_text("በጣም ጥሩ! አሁን ደግሞ ስልክ ቁጥርዎን (Phone Number) ያስገቡ፡")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("አድራሻዎን (Address / የሚኖሩበትን ከተማ ወይም ክፍለ ከተማ) ይጻፉልን፡")
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text
    reply_keyboard = [["ተማሪ", "ሰራተኛ"], ["ሌላ"]]
    await update.message.reply_text(
        "እርስዎ ተማሪ ነዎት ወይስ ሰራተኛ?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return STATUS

async def get_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["status"] = update.message.text
    user = update.message.from_user
    
    admin_notification = (
        "📥 *አዲስ ተመዝጋቢ ደርሷል!*\n\n"
        f"👤 *ስም:* {context.user_data.get('full_name')}\n"
        f"📞 *ስልክ:* {context.user_data.get('phone')}\n"
        f"📍 *አድራሻ:* {context.user_data.get('address')}\n"
        f"💼 *ሁኔታ:* {context.user_data.get('status')}\n"
        f"🔗 *Telegram:* @{user.username if user.username else 'የለውም'} (ID: {user.id})"
    )
    
    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text=admin_notification,
                parse_mode="Markdown",
            )
        except Exception as e:
            logging.error(f"Error sending to admin: {e}")

    await update.message.reply_text(
        "✅ *መረጃዎ በተሳካ ሁኔታ ተመዝግቧል! እናመሰግናለን።*\n\n"
        "አሁን ስለ ድርጅቱ (ALFA)፣ ስለ ፓኬጆች፣ ስለ ክፍያ እና ኮሚሽን አሰራር ወይም ስለ ስራው ማንኛውንም ጥያቄ መጠየቅ ይችላሉ። ምን ማወቅ ይፈልጋሉ?",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown",
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ምዝገባው ተቋርጧል። እንደገና ለመጀመር /start ይበሉ።")
    return ConversationHandler.END

async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    if not ai_model:
        await update.message.reply_text("ይቅርታ፣ የ AI አገልግሎት ለጊዜው አልተገናኘም። እባክዎ ትንሽ ቆይተው ይሞክሩ።")
        return

    try:
        # መረጃውን እና የተጠቃሚውን ጥያቄ አጣምሮ ለAI መላክ
        prompt = f"{SYSTEM_PROMPT}\n\nተጠቃሚው የጠየቀው ጥያቄ፦ {user_query}\nመልስ፦"
        response = ai_model.generate_content(prompt)
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"AI Error: {e}")
        await update.message.reply_text("ይቅርታ፣ ጥያቄዎን በማስተናገድ ላይ ችግር አጋጥሟል። እባክዎ እንደገና ይሞክሩ።")

async def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_status)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_chat))

    print("Ethio Remote job ቦት መስራት ጀምሯል...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    while True:
        await asyncio.sleep(3600)

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    main()
