import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), '.env'))

def send_telegram(order_num, order_sum):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    text = f"🚨 Крупный заказ! \nНомер: #{order_num}\nСумма: {order_sum} ₸"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"❌ Ошибка Telegram: {e}")

def sync():
    CRM_URL = f"{os.getenv('BASE_URL').rstrip('/')}/api/v5/orders"
    CRM_HEADERS = {"X-API-KEY": os.getenv('RETAILCRM_API_KEY')}
    SB_URL = f"{os.getenv('SUPABASE_URL').rstrip('/')}/rest/v1/orders"
    SB_HEADERS = {
        "apikey": os.getenv('SUPABASE_KEY'),
        "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
        "Content-Type": "application/json"
    }

    print("🔄 Запуск синхронизации...")
    res = requests.get(CRM_URL, headers=CRM_HEADERS)
    
    if res.status_code == 200:
        orders = res.json().get('orders', [])
        for o in orders:
            o_sum = float(o.get('totalSumm', 0))
            o_num = o.get('number')

            # 1. Уведомление 
            if o_sum > 50000:
                print(f"📢 Отправляю в Telegram заказ #{o_num}...")
                send_telegram(o_num, o_sum)

            # 2. База (пропускаем ошибки дубликатов)
            data = {
                "external_id": str(o_num),
                "customer_name": f"{o.get('firstName', '')}",
                "total_sum": o_sum,
                "status": o.get('status')
            }
            requests.post(SB_URL, headers=SB_HEADERS, json=data)
        
        print("\n✅ Синхронизация завершена!")
    else:
        print(f"❌ Ошибка CRM: {res.status_code}")

if __name__ == "__main__":
    sync()