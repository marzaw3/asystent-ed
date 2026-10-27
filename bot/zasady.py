"""Które wiadomości bot obsługuje i ile pytań może zadać gracz.

Bez zależności od discord.py, żeby dało się to łatwo testować.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

MIN_LENGTH = 3
MAX_LENGTH = 500


def should_handle(author_is_bot: bool, channel_id: int, content: str, question_channels: set[int]) -> bool:
    """Tak, gdy pisze człowiek, na kanale pytań, a pytanie ma od 3 do 500 znaków."""
    if author_is_bot:
        return False
    if channel_id not in question_channels:
        return False
    return MIN_LENGTH <= len(content.strip()) <= MAX_LENGTH


def should_handle_command(
    author_is_bot: bool, author_id: int, channel_id: int, command_channel_id: int, owner_id: int | None,
) -> bool:
    """Tak tylko dla właściciela na kanale poleceń. Boty (także Orion) - nigdy."""
    if author_is_bot or owner_id is None:
        return False
    return channel_id == command_channel_id and author_id == owner_id


def check_levels(levels, wiedza_dir: Path) -> list[str]:
    """Błędy w liście poziomów (po polsku). Pusta lista = wszystko w porządku.

    Plik poziomy.json może zmieniać Claude, więc pilnujemy, żeby plik_wiedzy
    wskazywał tylko na plik .md w folderze wiedzy - nigdy np. na .env.
    """
    if not isinstance(levels, list):
        return ["poziomy.json powinien zawierać listę poziomów."]

    errors = []
    numbers = set()
    wiedza_dir = wiedza_dir.resolve()
    for index, level in enumerate(levels, start=1):
        where = f"Poziom na pozycji {index}"
        if not isinstance(level, dict):
            errors.append(f"{where} nie jest obiektem.")
            continue
        number = level.get("numer")
        if not isinstance(number, int) or isinstance(number, bool) or number < 1:
            errors.append(f"{where}: „numer” musi być liczbą całkowitą od 1.")
        elif number in numbers:
            errors.append(f"{where}: numer {number} się powtarza.")
        else:
            numbers.add(number)
            where = f"Poziom {number}"
        if not isinstance(level.get("tytul"), str) or not level["tytul"].strip():
            errors.append(f"{where}: brakuje „tytul”.")
        channel_id = str(level.get("channel_id") or "")
        if channel_id and not channel_id.isdigit():
            errors.append(f"{where}: „channel_id” musi być pusty albo być liczbą.")

        file_name = level.get("plik_wiedzy")
        if not isinstance(file_name, str) or not file_name.strip():
            errors.append(f"{where}: brakuje „plik_wiedzy”.")
            continue
        path = (wiedza_dir.parent / file_name).resolve()
        if path.parent != wiedza_dir or path.suffix != ".md":
            errors.append(f"{where}: „plik_wiedzy” musi być plikiem .md w folderze wiedza/, a jest: „{file_name}”.")
        elif not path.is_file():
            errors.append(f"{where}: nie ma pliku {file_name}.")
    return errors


@dataclass(frozen=True)
class LimitSettings:
    cooldown_seconds: int
    daily_per_player: int
    daily_bot: int

    @classmethod
    def from_dict(cls, data: dict) -> "LimitSettings":
        """Rzuca ValueError z polskim opisem, gdy czegoś brakuje albo wartość nie jest liczbą."""
        keys = {
            "cooldown_seconds": "przerwa_sekund_na_gracza",
            "daily_per_player": "limit_dzienny_na_gracza",
            "daily_bot": "limit_dzienny_bota",
        }
        values = {}
        for field, key in keys.items():
            value = data.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"„{key}” musi być liczbą całkowitą 0 lub większą.")
            values[field] = value
        return cls(**values)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    message: str | None = None  # co odpisać graczowi, gdy pytanie nie jest przyjęte


class Limits:
    """Liczniki pytań: przerwa między pytaniami gracza, limit dzienny gracza i całego bota.

    Stan to tylko ID graczy, liczby i czas ostatniego pytania - bez nicków i treści.
    Liczniki zerują się o północy (czasu lokalnego).
    """

    def __init__(self, settings: LimitSettings, state: dict, save: Callable[[dict], None]) -> None:
        self.settings = settings
        self.state = state
        self.save = save

    def _start_day(self, today: str) -> None:
        complete = isinstance(self.state.get("bot"), int) and isinstance(self.state.get("gracze"), dict)
        if self.state.get("dzien") != today or not complete:
            self.state.clear()
            self.state.update({"dzien": today, "bot": 0, "gracze": {}})

    def check_and_count(self, user_id: int, now: datetime) -> Decision:
        """Sprawdza limity; gdy pytanie jest przyjęte, od razu je liczy i zapisuje stan."""
        self._start_day(now.date().isoformat())
        player = self.state["gracze"].get(str(user_id), {"pytania": 0, "ostatnie": None})

        if player["ostatnie"] is not None:
            waited = now.timestamp() - player["ostatnie"]
            if waited < self.settings.cooldown_seconds:
                left = max(1, round(self.settings.cooldown_seconds - waited))
                return Decision(False, f"Chwila przerwy! Następne pytanie możesz zadać za {left} s.")

        if player["pytania"] >= self.settings.daily_per_player:
            return Decision(
                False,
                f"Na dziś to już {self.settings.daily_per_player} pytań - świetna robota! "
                "Następne zadasz jutro, po północy.",
            )

        if self.state["bot"] >= self.settings.daily_bot:
            return Decision(
                False,
                "Orion odpowiedział dziś na bardzo dużo pytań i musi odpocząć. Zapytaj jutro, po północy!",
            )

        player["pytania"] += 1
        player["ostatnie"] = now.timestamp()
        self.state["gracze"][str(user_id)] = player
        self.state["bot"] += 1
        self.save(self.state)
        return Decision(True)

    def stats(self, now: datetime) -> dict:
        """Dzisiejsze liczby - bez ID graczy i bez treści pytań."""
        self._start_day(now.date().isoformat())
        counts = [player["pytania"] for player in self.state["gracze"].values()]
        return {
            "dzien": self.state["dzien"],
            "pytania": self.state["bot"],
            "limit_bota": self.settings.daily_bot,
            "gracze": len(counts),
            "gracze_na_limicie": sum(1 for count in counts if count >= self.settings.daily_per_player),
            "limit_gracza": self.settings.daily_per_player,
            "przerwa_sekund": self.settings.cooldown_seconds,
        }
