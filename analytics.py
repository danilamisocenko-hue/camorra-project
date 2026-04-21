import httpx
import time
import os

# База известных горячих кошельков (Binance, OKX, Bybit и др.)
EXCHANGES = {
    "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb": "Binance Hot",
    "THP6Un5GoNisbSbiXyE85S98WofInK9X": "Binance Hot 2",
    "TY679S9S6D3ASDF...": "OKX Hot",
    "TPYm9q73asdf...": "Bybit Hot",
    "TNAnv9asdf...": "Huobi Hot",
}

async def get_full_analytics(address, network):
    if network != 'TRC20': return "⚠️ Только TRC20"
    
    api_key = os.getenv("TRONGRID_KEY")
    headers = {"TRON-PRO-API-KEY": api_key} if api_key else {}
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Баланс сейчас
            acc = (await client.get(f"https://api.trongrid.io/v1/accounts/{address}", headers=headers)).json()
            balance = 0
            if 'data' in acc and acc['data']:
                for token in acc['data'][0].get('trc20', []):
                    if 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t' in token:
                        balance = int(token['TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t']) / 1_000_000
                        break
            
            # 2. Транзакции за 24ч
            tx_resp = await client.get(f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20", headers=headers)
            txs = tx_resp.json().get('data', [])
            
            now_ms = time.time() * 1000
            day_ago = now_ms - (86400 * 1000)
            
            stats = {"in": 0, "out": 0, "tx_in": 0, "tx_out": 0}
            for tx in txs:
                if tx['block_timestamp'] < day_ago: continue
                val = int(tx['value']) / 1_000_000
                if tx['to'] == address:
                    stats["in"] += val
                    stats["tx_in"] += 1
                else:
                    stats["out"] += val
                    stats["tx_out"] += 1

            # Оценка типа (биржа)
            wallet_type = "⚪️ Частный / Неизвестно"
            if address in EXCHANGES: 
                wallet_type = f"🏦 <b>{EXCHANGES[address]}</b>"
            elif stats['tx_in'] + stats['tx_out'] > 300: 
                wallet_type = "🏦 <b>Похоже на биржевой (High Activity)</b>"

            # Баланс 24ч назад
            old_balance = balance - stats['in'] + stats['out']

            return (
                f"📍 Сеть: <b>{network}</b>\n"
                f"📋 Адрес: <code>{address}</code>\n\n"
                f"💰 Баланс сейчас: <b>{balance:,.2f} USDT</b>\n"
                f"🕘 24ч назад: ~{old_balance:,.2f} USDT\n\n"
                f"📈 Вход за 24ч: {stats['in']:,.2f} USDT ({stats['tx_in']} tx)\n"
                f"📉 Выход за 24ч: {stats['out']:,.2f} USDT ({stats['tx_out']} tx)\n"
                f"➖ Чистый поток: {stats['in'] - stats['out']:+,.2f} USDT\n\n"
                f"🏦 Тип: {wallet_type}\n"
                f"🔌 Аналитика: ✅ активна"
            )
        except Exception as e:
            return f"❌ Ошибка API: {str(e)}"
