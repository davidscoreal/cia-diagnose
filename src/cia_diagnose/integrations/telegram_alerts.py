import httpx
import logging
import os

logger = logging.getLogger("cia-diagnose.telegram")

async def send_hot_call_alert(call_id: str, lead_name: str, score: float, reason: str):
    """Sends an immediate alert to Olivia/David when a call is getting hot."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        logger.error("Telegram credentials missing. Cannot send alert.")
        return False

    message = (
        f"🚨 *LLAMADA CALIENTE DETECTADA* 🚨\n\n"
        f"👤 *Lead:* {lead_name}\n"
        f"📞 *Call ID:* `{call_id}`\n"
        f"🔥 *Score:* {score}/100\n"
        f"💡 *Razón:* {reason}\n\n"
        f"👉 _Entra ahora a monitorear en Mission Control._"
    )

    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            await client.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False
