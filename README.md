Program zaczyna się od stworzenia jednostki klasy BudgetTrackerBot. 

Podczas inicjalizacji klasy rejestrowane są specjalne reguły (message handlers). Każda reguła reaguje na określony tekst wiadomości na czacie. Klasa zawiera również funkcje, które są wykonywane podczas aktywacji danej reguły (np. handle_start, handle_balance itp.). 

  

Linijka nr 190 wywołuje nieskończoną pętlę programu. Program cały czas sprawdza, czy otrzymana wiadomość odpowiada jednej z reguł. Jeśli tak, aktywowana jest przypisana do niej logika programu. 

  

Program korzysta z pliku data_functions, który został napisany przez Piotra Osmólskiego. Bot odwołuje się do tego pliku w celu zapisywania i odczytywania danych użytkownika.  

  

Kluczową rolę w programie odgrywają handlery — są to funkcje bota, które reagują na konkretne wiadomości od użytkownika. 

  

handle_start – reaguje na /start, wysyła powitanie oraz tworzy menu. 

  

handle_balance – reaguje na „💰 Saldo” i pokazuje saldo. 

  

handle_add_money – reaguje na „➕ Dodaj” i rozpoczyna dodawanie pieniędzy. 

  

handle_spend_money – reaguje na „➖ Wydaj” i rozpoczyna zapisywanie wydatku. 

  

handle_last_ten – reaguje na „📋 Ostatnie 10” i pokazuje ostatnie transakcje. 

  

handle_help – reaguje na „❓ Pomoc” i wysyła instrukcję. 

  

handle_command – reaguje na komendy tekstowe: /balance, /add, /spend, /last. 
