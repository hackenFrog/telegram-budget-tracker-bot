"""
Klasy do obsługi danych użytkownika w stylu OOP.
"""

import json
import os
from datetime import datetime

DB_FILE = "budget_data.json"


class Transaction:
    """Reprezentuje jedną transakcję finansową."""

    def __init__(self, trans_type: str, amount: float, desc: str):
        self.type = trans_type  # "+" lub "-"
        self.amount = amount
        self.desc = desc or "(bez opisu)"
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M")

    def __str__(self) -> str:
        """Formatuje transakcję do wyświetlenia."""
        sign = self.type
        return f"{self.date} | {sign}{self.amount} zł | {self.desc}"


class User:
    """Reprezentuje użytkownika z jego saldem i transakcjami."""

    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self.balance = 0.0
        self.transactions: list[Transaction] = []

    def add_income(self, amount: float, desc: str) -> float:
        """Dodaje przychód do konta."""
        self.balance += amount
        self.transactions.append(Transaction("+", amount, desc))
        return self.balance

    def add_expense(self, amount: float, desc: str) -> float:
        """Odejmuje wydatek z konta (z walidacją)."""
        if amount > self.balance:
            raise ValueError("Niewystarczające środki")
        self.balance -= amount
        self.transactions.append(Transaction("-", amount, desc))
        return self.balance

    def get_last_transactions(self, limit: int = 10) -> list[str]:
        """Zwraca ostatnie N transakcji jako sformatowane stringi."""
        recent = self.transactions[-limit:]
        return [str(t) for t in reversed(recent)]


class BudgetTracker:
    """
    GŁÓWNY MENEDŻER BUDŻETU
    
    To jest "mózg" całego systemu. Zarządza wszystkimi użytkownikami.
    Funkcje:
    - Przechowuje dane wszystkich użytkowników
    - Zapisuje dane do pliku JSON (trwała pamięć)
    - Wczytuje dane z pliku przy starcie
    - Tworzy nowych użytkowników automatycznie
    
    Dzięki tej klasie dane nie giną po wyłączeniu bota!
    """

    def __init__(self):
        """Tworzy menedżera i od razu wczytuje zapisane dane z pliku."""
        self.users: dict[int, User] = {}  # Słownik wszystkich użytkowników
        self.load()  # Wczytaj dane z budget_data.json

    def load(self):
        """
        Wczytuje wszystkie dane użytkowników z pliku JSON.
        Jeśli plik nie istnieje (pierwszy start) - nic się nie dzieje.
        Odtwarza obiekty User i Transaction z zapisanych danych.
        """
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for chat_id_str, user_data in data.items():
                    chat_id = int(chat_id_str)
                    user = User(chat_id)
                    user.balance = user_data["balance"]
                    for tx_data in user_data["transactions"]:
                        tx = Transaction(
                            tx_data["type"],
                            tx_data["amount"],
                            tx_data["desc"]
                        )
                        tx.date = tx_data["date"]
                        user.transactions.append(tx)
                    self.users[chat_id] = user

    def save(self):
        """
        Zapisuje wszystkie dane użytkowników do pliku JSON.
        Wywoływana po każdej operacji (dodanie pieniędzy, wydatek, nowy użytkownik).
        Dzięki temu dane są zawsze aktualne i bezpieczne.
        """
        data = {}
        for chat_id, user in self.users.items():
            data[str(chat_id)] = {
                "balance": user.balance,
                "transactions": [
                    {
                        "type": tx.type,
                        "amount": tx.amount,
                        "desc": tx.desc,
                        "date": tx.date
                    }
                    for tx in user.transactions
                ]
            }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_or_create_user(self, chat_id: int) -> User:
        """Zwraca istniejącego użytkownika lub tworzy nowego."""
        if chat_id not in self.users:
            self.users[chat_id] = User(chat_id)
            self.save()
        return self.users[chat_id]

    def get_balance(self, chat_id: int) -> float:
        """Zwraca saldo użytkownika."""
        user = self.get_or_create_user(chat_id)
        return user.balance

    def add_transaction(self, chat_id: int, amount: float, desc: str) -> float:
        """Dodaje przychód (pozytywną transakcję)."""
        user = self.get_or_create_user(chat_id)
        result = user.add_income(amount, desc)
        self.save()
        return result

    def spend_transaction(self, chat_id: int, amount: float, desc: str) -> float:
        """Rejestruje wydatek (ujemną transakcję)."""
        user = self.get_or_create_user(chat_id)
        result = user.add_expense(amount, desc)
        self.save()
        return result

    def last_transactions(self, chat_id: int, limit: int = 10) -> list[str]:
        """Zwraca ostatnie N transakcji użytkownika."""
        user = self.get_or_create_user(chat_id)
        return user.get_last_transactions(limit)


# Globalna instancja trackera (kompatybilność z istniejącym kodem)
tracker = BudgetTracker()


# Funkcje kompatybilności dla istniejącego kodu
def ensure_user(chat_id: int) -> None:
    """Zapewnia istnienie użytkownika (dla kompatybilności wstecznej)."""
    tracker.get_or_create_user(chat_id)


def get_balance(chat_id: int) -> float:
    """Zwraca saldo użytkownika (dla kompatybilności wstecznej)."""
    return tracker.get_balance(chat_id)


def add_transaction(chat_id: int, amount: float, desc: str) -> float:
    """Dodaje przychód (dla kompatybilności wstecznej)."""
    return tracker.add_transaction(chat_id, amount, desc)


def spend_transaction(chat_id: int, amount: float, desc: str) -> float:
    """Rejestruje wydatek (dla kompatybilności wstecznej)."""
    return tracker.spend_transaction(chat_id, amount, desc)


def last_transactions(chat_id: int, limit: int = 10) -> list[str]:
    """Zwraca ostatnie N transakcji (dla kompatybilności wstecznej)."""
    return tracker.last_transactions(chat_id, limit)
