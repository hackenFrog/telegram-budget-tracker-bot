

"""
Autor: Arsen Drahomeretskyi
""""

import os
from dotenv import load_dotenv
import telebot
from telebot import types
import data_functions as df

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


class BudgetTrackerBot:
    """Bot Telegram do zarządzania budżetem osobistym."""

    def __init__(self, token: str):
        self.bot = telebot.TeleBot(token)
        self.pending = {}  # Stan wieloetapowych operacji
        self._register_handlers()

    def _register_handlers(self):
        """Rejestruje wszystkie handlery wiadomości."""
        self.bot.message_handler(commands=['start'])(self.handle_start)
        self.bot.message_handler(
            func=lambda msg: msg.text == "💰 Saldo")(self.handle_balance)
        self.bot.message_handler(func=lambda msg: msg.text == "➕ Dodaj")(
            self.handle_add_money)
        self.bot.message_handler(func=lambda msg: msg.text == "➖ Wydaj")(
            self.handle_spend_money)
        self.bot.message_handler(
            func=lambda msg: msg.text == "📋 Ostatnie 10")(self.handle_last_ten)
        self.bot.message_handler(
            func=lambda msg: msg.text == "❓ Pomoc")(self.handle_help)
        self.bot.message_handler(
            commands=['balance', 'add', 'spend', 'last'])(self.handle_command)
        self.bot.message_handler(func=lambda msg: True)(self.handle_default)

    def _get_main_keyboard(self) -> types.ReplyKeyboardMarkup:
        """Zwraca główne menu z przyciskami."""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("💰 Saldo", "➕ Dodaj")
        keyboard.add("➖ Wydaj", "📋 Ostatnie 10")
        keyboard.add("❓ Pomoc")
        return keyboard

    def handle_start(self, msg):
        """Komenda /start - Inicjalizacja użytkownika."""
        chat_id = msg.chat.id
        df.ensure_user(chat_id)

        keyboard = self._get_main_keyboard()
        self.bot.send_message(
            chat_id, "👋 Cześć! Pomogę Ci zarządzać pieniędzmi!", reply_markup=keyboard)

    def handle_balance(self, msg):
        """Obsługa: Sprawdzenie salda."""
        chat_id = msg.chat.id
        bal = df.get_balance(chat_id)
        self.bot.send_message(chat_id, f"💰 Twoje saldo: {bal} zł")

    def handle_add_money(self, msg):
        """Obsługa: Rozpoczęcie dodawania pieniędzy."""
        chat_id = msg.chat.id
        df.ensure_user(chat_id)
        msg_text = self.bot.send_message(
            chat_id, "Ile pieniędzy dodać? (wpisz liczbę)")
        self.bot.register_next_step_handler(msg_text, self.process_add_amount)

    def process_add_amount(self, msg):
        """Krok 1 dodawania: Pobierz kwotę."""
        try:
            amount = float(msg.text)
            if amount > 0:
                self.pending[msg.chat.id] = {"type": "+", "amount": amount}
                msg_text = self.bot.send_message(
                    msg.chat.id, "Napisz krótki opis transakcji:")
                self.bot.register_next_step_handler(
                    msg_text, self.process_add_desc)
            else:
                self.bot.send_message(
                    msg.chat.id, "❌ Liczba musi być większa od 0!")
        except ValueError:
            self.bot.send_message(msg.chat.id, "❌ Błąd! Wpisz liczbę!")

    def process_add_desc(self, msg):
        """Krok 2 dodawania: Pobierz opis i dodaj transakcję."""
        data = self.pending.pop(msg.chat.id, None)
        if not data:
            self.bot.send_message(
                msg.chat.id, "❌ Brak aktywnej transakcji. Naciśnij ➕ Dodaj.")
            return

        desc = msg.text.strip()
        bal = df.add_transaction(msg.chat.id, data["amount"], desc)
        self.bot.send_message(
            msg.chat.id,
            f"✅ Dodano {data['amount']} zł!\n💰 Saldo: {bal} zł"
        )

    def handle_spend_money(self, msg):
        """Obsługa: Rozpoczęcie wydawania pieniędzy."""
        chat_id = msg.chat.id
        df.ensure_user(chat_id)
        msg_text = self.bot.send_message(chat_id, "Ile wydać? (wpisz liczbę)")
        self.bot.register_next_step_handler(
            msg_text, self.process_spend_amount)

    def process_spend_amount(self, msg):
        """Krok 1 wydawania: Pobierz kwotę."""
        try:
            amount = float(msg.text)
            if amount > 0:
                if amount <= df.get_balance(msg.chat.id):
                    self.pending[msg.chat.id] = {"type": "-", "amount": amount}
                    msg_text = self.bot.send_message(
                        msg.chat.id, "Napisz krótki opis transakcji:")
                    self.bot.register_next_step_handler(
                        msg_text, self.process_spend_desc)
                else:
                    self.bot.send_message(
                        msg.chat.id, f"❌ Za mało pieniędzy! Masz tylko {df.get_balance(msg.chat.id)} zł")
            else:
                self.bot.send_message(
                    msg.chat.id, "❌ Liczba musi być większa od 0!")
        except ValueError:
            self.bot.send_message(msg.chat.id, "❌ Błąd! Wpisz liczbę!")

    def process_spend_desc(self, msg):
        """Krok 2 wydawania: Pobierz opis i wykonaj transakcję."""
        data = self.pending.pop(msg.chat.id, None)
        if not data:
            self.bot.send_message(
                msg.chat.id, "❌ Brak aktywnej transakcji. Naciśnij ➖ Wydaj.")
            return

        desc = msg.text.strip()
        try:
            bal = df.spend_transaction(msg.chat.id, data["amount"], desc)
            self.bot.send_message(
                msg.chat.id,
                f"✅ Wydano {data['amount']} zł!\n💰 Saldo: {bal} zł"
            )
        except ValueError:
            self.bot.send_message(msg.chat.id, "❌ Za mało pieniędzy!")

    def handle_last_ten(self, msg):
        """Obsługa: Pokaż ostatnie 10 transakcji."""
        chat_id = msg.chat.id
        lines = df.last_transactions(chat_id, 10)
        if not lines:
            self.bot.send_message(chat_id, "📋 Brak transakcji.")
            return
        self.bot.send_message(
            chat_id, "📋 Ostatnie 10 transakcji:\n" + "\n".join(lines))

    def handle_help(self, msg):
        """Obsługa: Wyświetl pomoc."""
        text = (
            "📚 Jak używać:\n\n"
            "💰 Saldo - pokazuje Twoje pieniądze\n"
            "➕ Dodaj - dodaj pieniądze\n"
            "➖ Wydaj - wydaj pieniądze\n"
            "📋 Ostatnie 10 - pokaż transakcje\n\n"
            "✨ Użyj przycisków! Po prostu kliknij!"
        )
        self.bot.send_message(msg.chat.id, text)

    def handle_command(self, msg):
        """Obsługa komend: /balance, /add, /spend, /last."""
        if msg.text == '/balance':
            self.handle_balance(msg)
        elif msg.text == '/add':
            self.handle_add_money(msg)
        elif msg.text == '/spend':
            self.handle_spend_money(msg)
        elif msg.text == '/last':
            self.handle_last_ten(msg)

    def handle_default(self, msg):
        """Obsługa: Domyślna odpowiedź na inne wiadomości."""
        self.bot.send_message(
            msg.chat.id, "❓ Nie rozumiem. Użyj przycisków lub wpisz /start")

    def start(self):
        """Uruchomia bota."""
        print("🤖 Bot uruchomiony! Napisz do bota na Telegramie...")
        self.bot.infinity_polling()


if __name__ == "__main__":
    bot = BudgetTrackerBot(TOKEN)
    bot.start()

