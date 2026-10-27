"""Kanał poleceń: prośby właściciela do Claude Code i polecenia z wykrzyknikiem.

Z tego kanału korzysta tylko właściciel (DISCORD_OWNER_ID). Claude działa w głównym
folderze repozytorium, ale może czytać tylko gra/ i bot/ i zmieniać tylko pliki wiedzy
oraz poziomy.json. Każda prośba to osobne wywołanie - bez pamięci poprzednich rozmów.
"""

OWNER_TIMEOUT_SECONDS = 5 * 60

COMMANDS = {
    "!statystyki": "statystyki",
    "!pauza": "pauza",
    "!wznow": "wznow",
    "!wznów": "wznow",
}

OWNER_CONTEXT = """\
Jesteś asystentem bota Discord „Orion” - pomocnika z fizyki do gry Misja Orion dla uczniów 7 klasy.
Piszesz do właściciela bota: po polsku, krótko. Folder roboczy to główny folder repozytorium.

Co możesz robić:
- odpowiadać na pytania o grę (pliki gra/dynamika-poziomN.html) i o bota (folder bot/),
- poprawiać pliki wiedzy bot/wiedza/poziom-N.md,
- dopisywać nowe poziomy do bot/poziomy.json.

Zasady:
- Wiedzę bierzesz tylko z plików gry w folderze gra/. Nie dopisujesz materiału spoza gry
  ani gotowych wyników zadań z gry (wyników liczbowych, poprawnych odpowiedzi).
- Format bot/poziomy.json - lista obiektów, np.:
  {"numer": 7, "tytul": "<nagłówek h1 z ekranu startowego poziomu>", "plik_wiedzy": "wiedza/poziom-7.md", "channel_id": ""}
- Nowemu poziomowi NIE wpisujesz channel_id - zostaw "". Kanał na Discordzie zakłada bot.
- Plik wiedzy ma nagłówki: „# Poziom N: tytuł”, „**Moduł:**”, „**Temat z fizyki:**”, „**Podręcznik:**”,
  „## Pojęcia”, „## Wzory”, „## Przykłady i sytuacje z fabuły”, „## Typowe błędy”, „## Wskazówki z gry”.
- Nie czytasz plików .env.
- Na koniec napisz krótko, co zrobiłeś i które pliki zmieniłeś.
"""


def owner_args() -> list[str]:
    return [
        "-p",
        "--permission-mode", "dontAsk",
        "--tools", "Read,Edit,Write",
        "--allowedTools",
        "Read(./gra/**),Read(./bot/**),Edit(./bot/poziomy.json),Write(./bot/wiedza/**),Edit(./bot/wiedza/**)",
        "--disallowedTools",
        "Bash,Read(./.env),Read(./.env.txt),Read(./zdjecia/**),Read(./grafika/**)",
        "--strict-mcp-config",
        "--max-turns", "15",
        "--no-session-persistence",
    ]


def build_owner_input(request: str) -> str:
    return f"{OWNER_CONTEXT}\n<prosba_wlasciciela>\n{request.strip()}\n</prosba_wlasciciela>\n"


def parse_command(content: str) -> str | None:
    """„!statystyki”, „!pauza”, „!wznow” -> nazwa polecenia; inna wiadomość -> None (idzie do Claude)."""
    return COMMANDS.get(content.strip().lower())
