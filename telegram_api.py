import requests
TOKEN = "5503993388:AAEhkd7Q_b7iYrAowBdC5QsMM35UJl0uknw"
CHAT_ID = "-808085014" # PROD
# CHAT_ID = "-814886566" # TEST

def send_message(message, chat_id=CHAT_ID):
    api_url = f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}'
    requests.get(api_url, timeout=10).json()


# send_message("test_telegram")
