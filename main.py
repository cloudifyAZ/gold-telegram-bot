from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import threading
import json

# === Telegram Ayarları ===
BOT_TOKEN = "8397760596:AAFbi6HIMXvQAPVAgjoljBarvOJeNeYwwz0"
user_data = {
    "balance": None,
    "trade_size": None,
    "leverage": None,
    "open_trades": [],
    "history": []
}

# === Flask Sunucusu ===
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    signal = data.get("signal")

    if signal == "BUY":
        open_trade("long")
    elif signal == "SELL":
        open_trade("short")
    elif signal == "CLOSE":
        close_trades()

    return "ok", 200

def open_trade(direction):
    if not user_data["balance"]:
        return

    trade_value = user_data["trade_size"]
    leverage = user_data["leverage"]
    position_value = trade_value * leverage

    user_data["balance"] -= trade_value  # marjin düş
    user_data["open_trades"].append({
        "type": direction,
        "value": trade_value,
        "leverage": leverage
    })

def close_trades():
    profit = 0
    for trade in user_data["open_trades"]:
        # Demo kar hesaplama (örnek olarak rastgele kazanç/kayıp)
        import random
        change = random.uniform(-0.05, 0.05)  # ±5%
        result = trade["value"] * trade["leverage"] * change
        profit += result
        user_data["history"].append(result)

    user_data["balance"] += (sum(t["value"] for t in user_data["open_trades"]) + profit)
    user_data["open_trades"] = []

# === Telegram Komutları ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏁 Başlayalım! Lütfen başlangıç bakiyeni gir (örnek: 300):")
    context.user_data["step"] = "balance"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    step = context.user_data.get("step")

    if step == "balance":
        user_data["balance"] = float(text)
        await update.message.reply_text("💰 Her işlem için yatırım miktarını yaz (örnek: 4):")
        context.user_data["step"] = "trade_size"

    elif step == "trade_size":
        user_data["trade_size"] = float(text)
        await update.message.reply_text("⚙️ Kaldıraç seç (örnek: 10, 100, 1000, 10000):")
        context.user_data["step"] = "leverage"

    elif step == "leverage":
        user_data["leverage"] = int(text)
        context.user_data["step"] = None
        await update.message.reply_text("✅ Ayarlandı! Artık sinyalleri bekliyoruz.\nTradingView'den webhook sinyali geldiğinde işlemler otomatik yapılacak.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = user_data["balance"] or 0
    total_profit = sum(user_data["history"])
    trade_count = len(user_data["history"])
    await update.message.reply_text(
        f"📊 Rapor:\n"
        f"Toplam İşlem: {trade_count}\n"
        f"Toplam Kar/Zarar: {total_profit:.2f}$\n"
        f"Şu anki Bakiye: {balance:.2f}$"
    )

# === Telegram Bot Thread ===
def run_telegram():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("rapor", report))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(app_bot.run_polling())

# === Flask Thread ===
def run_flask():
    app.run(host="0.0.0.0", port=5000)

# === Çalıştır ===
if __name__ == "__main__":
    threading.Thread(target=run_telegram).start()
    threading.Thread(target=run_flask).start()


