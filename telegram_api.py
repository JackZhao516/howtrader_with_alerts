import requests
token = "5503993388:AAEhkd7Q_b7iYrAowBdC5QsMM35UJl0uknw"
chat_id = "-814886566"


def send_message(message):
    api_url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}'
    requests.get(api_url, timeout=10).json()


send_message("test_telegram")
