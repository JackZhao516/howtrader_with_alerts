import requests


class TelegramBot:
    TOKEN = "5503993388:AAEhkd7Q_b7iYrAowBdC5QsMM35UJl0uknw"
    TELEGRAM_CHAT_ID_PROD_ALERT = "-808085014"  # PROD Alert
    TELEGRAM_CHAT_ID_PROD_SUM = "-804953236"  # PROD Summary
    TELEGRAM_CHAT_ID_TEST = "-814886566"  # TEST

    def __init__(self, prod=True, alert=True):
        self.telegram_chat_id = self.TELEGRAM_CHAT_ID_TEST if not prod else \
            (self.TELEGRAM_CHAT_ID_PROD_ALERT if alert else self.TELEGRAM_CHAT_ID_PROD_SUM)

    def send_message(self, message):
        api_url = f'https://api.telegram.org/bot{self.TOKEN}/sendMessage?chat_id={self.telegram_chat_id}&text={message}'
        requests.get(api_url, timeout=10).json()
