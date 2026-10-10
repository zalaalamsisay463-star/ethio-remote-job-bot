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
BOT_TOKEN = "8640220728:AAEbJYYFGdkkk5-DVl6W2RpbgNA6XK9S4-s"
GEMINI_API_KEY = "AQ.Ab8RN6K1XNjabBROtMZCaDhpwS6SDmqZ8cw39cesRLymeHnIwg"  # ያንተን ሙሉ ቁልፍ እዚህ አስገባ
ADMIN_CHAT_ID = "8613322776"

# Gemini ማዋቀር
try:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    logging.error(f"AI config error: {e}")
    ai_model = None

# Render እንዳይዘጋው Dummy Server
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

# የመጽሐፉ ሙሉ የእውቀት ማዕከል (የተሟላ መረጃ)
FULL_KNOWLEDGE_BASE = """
ስለ አልፋ (ALFA) አለም አቀፍ ድርጅት እና ቀጥተኛ ሽያጭ ሙሉ መረጃ፦

1. ስለ ድርጅቱ (ALFA)፦
- አልፋ አለም አቀፍ የቀጥተኛ ሽያጭ (Direct Selling / Network Marketing) ድርጅት ነው።
- ዋና መስሪያ ቤቱ በአሜሪካ የሚገኝ ሲሆን በአፍሪካ የመጀመሪያ ቅርንጫፉን በኢትዮጵያ በይፋ ከፍቷል።
- ወደ ሱዳን፣ ኬንያ፣ ሶማሊያ፣ እስራኤል፣ አንጎላ እና ኡጋንዳ በስፋት ለመስፋፋት እቅድ አለው።
- በኢትዮጵያ ንግድና ቀጠናዊ ትስስር ሚኒስቴር ሙሉ ህጋዊ ፈቃድ ያለው ድርጅት ነው።

2. የግብይት ልዩነት (ቀጥተኛ ሽያጭ ከባህላዊ ንግድ)፦
- ባህላዊ ግብይት፦ ምርት ከአምራች ተነስቶ በዋና ጅምላ ሻጭ፣ በችርቻሮ ሻጭ እና በውድ ማስታወቂያዎች በኩል አልፎ ሸማቹ ጋር ሲደርስ ዋጋው ይንራል።
- ቀጥተኛ ሽያጭ፦ ምርት ከአምራች በቀጥታ ወደ ተጠቃሚ ይደርሳል። በመሃል ያለውን የማስታወቂያና የደላሎች ወጪ ለአባላትና ለተጠቃሚዎች በኮሚሽን መልክ ያከፋፍላል።

3. የአባልነት ፓኬጆች እና ዋጋዎች፦
- የሎው (Yellow)፦ ዋጋው $110 ሲሆን 11% ዙር ኮሚሽን ይሰጣል (ሳምንታዊ ጣሪያ $1,000)።
- ኦሬንጅ (Orange)፦ ዋጋው $210 ሲሆን 12% ዙር ኮሚሽን ይሰጣል (ሳምንታዊ ጣሪያ $2,000)።
- ግሪን (Green)፦ ዋጋው $410 ሲሆን 14% ዙር ኮሚሽን ይሰጣል (ሳምንታዊ ጣሪያ $4,000)።
- ጎልደን (Golden)፦ ዋጋው $810 ሲሆን 15% ዙር ኮሚሽን ይሰጣል (ሳምንታዊ ጣሪያ $5,000)።

4. የገቢና የኮሚሽን አሰራር፦
- የቀጥተኛ ማስታወቂያ ጉርሻ (Direct Bonus)፦ አዲስ ሰው ሲጋብዙ ከ 16% እስከ 19% ቀጥተኛ ጉርሻ ያገኛሉ።
- የዙር ኮሚሽን (Cycle Bonus)፦ በግራ ቡድን 600 ነጥብ፣ በቀኝ ቡድን 600 ነጥብ ሲመጣጠን 1 ዙር (Cycle) ተብሎ እንደ ፓኬጅዎ መቶኛ ክፍያ ይፈጸማል።

5. የደረጃ እድገቶችና ከፍተኛ ሽልማቶች፦
- መነሻ ደረጃዎች፦ CT (Consultant) -> MT (Manager) -> TT (Team Leader)
- NTB፦ $5,000 የቢሮ ድጎማ ወይም የውጭ ሀገር ጉዞ
- IBB፦ $10,000 የቢሮ ድጎማ + $15,000 የመኪና ሽልማት
- GEB፦ $20,000 የቢሮ ድጎማ + $25,000 የመኪና ሽልማት
- CA፦ $50,000 የቢሮ ድጎማ + $100,000 ዶላር የገንዘብ ሽልማት
- AL (Alpha Legend)፦ $100,000 የቢሮ ድጎማ + $500,000 ዶላር የህይወት ዘመን ሽልማት

6. ምርቶች፦
- ከፍተኛ ጥራት ያላቸው የተፈጥሮ ጤና መጠበቂያዎች
- የተለያዩ ውበት መጠበቂያና ኮስሞቲክስ ምርቶች
- አዳዲስ የቴክኖሎጂ ውጤቶች (ለምሳሌ የአየር ላይ ግሎብ - Magnetic Levitation Globe)
- የአእምሮ እድገት እና የአመራር ብቃት (Leadership) ስልጠናዎች

7. መተግበሪያና ድጋፍ፦
- ሲ.ኤፍ.ኤስ (CFS App) በ Google Play Store የሚገኝ ሲሆን የደንበኞች ክትትልና የቅሬታ መፍቻ ነው።
- 8ቱ የግብዣ ስልቶች (ፍጥነት፣ ማድነቅ፣ መጋበዝ፣ "እንዲህ ባደርግልህ... ታደርጋለህ?" የሚል አቀራረብ፣ የጊዜ ቀጠሮ ማረጋገጥና ስልክ መዝጋት)።
"""

# AI በማይሰራበት ጊዜ በቀጥታ ፈጣን መልስ የሚሰጡ ዝግጁ መልሶች
FALLBACK_ANSWERS = {
    "ድርጅት": "🏢 *ስለ አልፋ (ALFA) ድርጅት፦*\n\nአልፋ ዋና ቢሮው አሜሪካ የሚገኝ አለም አቀፍ የቀጥተኛ ሽያጭ (Direct Selling) ድርጅት ሲሆን በአፍሪካ የመጀመሪያ ቅርንጫፉን በኢትዮጵያ በይፋ ከፍቷል። ድርጅቱ ህጋዊ የንግድ ፈቃድ ያለው ሲሆን ወደ ሌሎች የአፍሪካ ሀገራትም በመስፋፋት ላይ ይገኛል።",
    "ፓኬጅ": "📦 *የአባልነት ፓኬጆች፦*\n\n1. *Yellow ($110)* - 11% ዙር ኮሚሽን (ሳምንታዊ ጣሪያ $1,000)\n2. *Orange ($210)* - 12% ዙር ኮሚሽን (ሳምንታዊ ጣሪያ $2,000)\n3. *Green ($410)* - 14% ዙር ኮሚሽን (ሳምንታዊ ጣሪያ $4,000)\n4. *Golden ($810)* - 15% ዙር ኮሚሽን (ሳምንታዊ ጣሪያ $5,000)",
    "ክፍያ": "💰 *የክፍያና ኮሚሽን አሰራር፦*\n\n- *ቀጥተኛ ማስታወቂያ ጉርሻ፦* አዲስ አባል ሲጋብዙ ከ 16% እስከ 19% ጉርሻ ይሰጣል።\n- *የዙር ኮሚሽን (Cycle)፦* በግራ 600 ነጥብ፣ በቀኝ 600 ነጥብ ሲመጣጠን እንደ ፓኬጅዎ መቶኛ ሳምንታዊ ገቢ ያገኛሉ።",
    "ሽልማት": "🏆 *የደረጃ እድገቶችና ሽልማቶች፦*\n\n- *NTB፦* $5,000 የቢሮ ድጎማ ወይም ጉዞ\n- *IBB፦* $10,000 ቢሮ + $15,000 መኪና\n- *GEB፦* $20,000 ቢሮ + $25,000 መኪና\n- *CA፦* $50,000 ቢሮ + $100,000 ዶላር\n- *Alpha Legend፦* $100,000 ቢሮ + $500,000 ዶላር ሽልማት!",
    "ምርት": "🛍 *ምርቶች፦*\n\n- የጤና መጠበቂያዎች\n- የተፈጥሮ ኮስሞቲክስ\n- ዘመናዊ የቴክኖሎጂ ውጤቶች (የአየር ላይ ግሎብ)\n- የአመራርና የአእምሮ ስልጠናዎች",
}

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
    user_query = update.message.text.lower()
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # 1. መጀመሪያ በ AI ለመመለስ መሞከር
    if ai_model:
        try:
            prompt = f"አንተ Ethio Remote job ረዳት ነህ። የሚከተለውን ሙሉ መረጃ ተጠቅመህ ጥያቄውን በአማርኛ መልስ።\n\nመረጃ፦\n{FULL_KNOWLEDGE_BASE}\n\nየተጠቃሚ ጥያቄ፦ {user_query}\nመልስ፦"
            response = ai_model.generate_content(prompt)
            if response and response.text:
                await update.message.reply_text(response.text)
                return
        except Exception as e:
            logging.error(f"AI call failed: {e}")

    # 2. AI ባይመልስ እንኳን በኮዱ ውስጥ ከተካተተው ሙሉ መረጃ በቀጥታ መመለስ
    for key, answer in FALLBACK_ANSWERS.items():
        if key in user_query:
            await update.message.reply_text(answer, parse_mode="Markdown")
            return

    # አጠቃላይ ማብራሪያ
    await update.message.reply_text(
        f"ℹ️ *ስለ ALFA እና ስራው የተሟላ መረጃ፦*\n{FULL_KNOWLEDGE_BASE}",
        parse_mode="Markdown",
    )

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
