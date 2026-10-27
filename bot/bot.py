"""Bot Discord „Orion” - pomocnik z fizyki do gry Misja Orion."""

import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import discord
from dotenv import dotenv_values

BOT_DIR = Path(__file__).resolve().parent
REPO_DIR = BOT_DIR.parent
ENV_FILE = REPO_DIR / ".env"
POZIOMY_FILE = BOT_DIR / "poziomy.json"
STAN_DIR = BOT_DIR / "stan"
KANALY_FILE = STAN_DIR / "kanaly.json"

ONLINE_MESSAGE = "Orion online - pytaj o fizykę!"
CATEGORY_NAME = "Misja Orion"
ASK_CHANNEL_NAME = "zapytaj-oriona"
AI_NOTE = "Odpowiada sztuczna inteligencja. Może się pomylić, więc sprawdzaj odpowiedzi w podręczniku."


@dataclass(frozen=True)
class Settings:
    token: str
    guild_id: int
    owner_id: int | None
    command_channel_id: int


def fail(message: str) -> None:
    """Wypisuje zrozumiały komunikat i kończy program."""
    print(f"BŁĄD: {message}", file=sys.stderr)
    sys.exit(1)


def warn(message: str) -> None:
    print(f"UWAGA: {message}", file=sys.stderr)


def read_id(values: dict, key: str, required: bool) -> int | None:
    raw = (values.get(key) or "").strip()
    if not raw:
        if required:
            fail(f"W pliku .env brakuje wartości {key}.")
        return None
    if not raw.isdigit():
        fail(f"{key} w pliku .env musi być liczbą (ID z Discorda), a jest: „{raw}”.")
    return int(raw)


def load_settings() -> Settings:
    if not ENV_FILE.is_file():
        fail(
            f"Nie znaleziono pliku .env w folderze {REPO_DIR}.\n"
            "Skopiuj bot/.env.example jako .env do głównego folderu repozytorium i uzupełnij wartości."
        )

    values = dotenv_values(ENV_FILE, encoding="utf-8")

    token = (values.get("DISCORD_TOKEN") or "").strip()
    if not token:
        fail("W pliku .env brakuje tokenu bota (DISCORD_TOKEN).")

    return Settings(
        token=token,
        guild_id=read_id(values, "DISCORD_GUILD_ID", required=True),
        owner_id=read_id(values, "DISCORD_OWNER_ID", required=False),
        command_channel_id=read_id(values, "DISCORD_COMMAND_CHANNEL_ID", required=True),
    )


# --- pliki JSON (UTF-8) -------------------------------------------------------

def read_json(path: Path, default):
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(f"Plik {path.name} ma błąd w zapisie JSON (linia {error.lineno}): {error.msg}.")


def write_json(path: Path, data) -> None:
    """Zapisuje przez plik tymczasowy, żeby przerwany zapis nie zepsuł pliku."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_levels() -> list[dict]:
    levels = read_json(POZIOMY_FILE, None)
    if not isinstance(levels, list):
        fail(f"Nie znaleziono listy poziomów w pliku {POZIOMY_FILE.name}.")
    return levels


# --- pomocnicze ---------------------------------------------------------------

def slugify(text: str) -> str:
    """„Orion ma awarię!” -> „orion-ma-awarie” (małe litery, bez polskich znaków)."""
    text = text.lower().replace("ł", "l")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def level_channel_name(level: dict) -> str:
    return f"poziom-{level['numer']}-{slugify(level['tytul'])}"


def level_topic(level: dict) -> str | None:
    """Krótki temat z pliku wiedzy: „**Moduł:** Moduł 1: I zasada dynamiki Newtona” -> „I zasada dynamiki Newtona”."""
    path = BOT_DIR / level["plik_wiedzy"]
    if not path.is_file():
        return None
    match = re.search(r"\*\*Moduł:\*\*\s*(?:Moduł \d+:\s*)?(.+)", path.read_text(encoding="utf-8"))
    return match.group(1).strip().rstrip(".") if match else None


def parse_channel_id(value) -> int | None:
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None


# --- bot ----------------------------------------------------------------------

class Orion(discord.Client):
    def __init__(self, settings: Settings) -> None:
        super().__init__(intents=discord.Intents.default())
        self.settings = settings
        self.started = False

    async def on_ready(self) -> None:
        print(f"Zalogowano jako {self.user} (ID: {self.user.id}).")

        # on_ready wywołuje się też po każdym ponownym połączeniu - start robimy raz.
        if self.started:
            return
        self.started = True

        await self.setup_channels()
        await self.send_online_message()

    async def setup_channels(self) -> None:
        guild = self.get_guild(self.settings.guild_id)
        if guild is None:
            warn(
                f"Bot nie jest na serwerze o ID {self.settings.guild_id}. "
                "Sprawdź DISCORD_GUILD_ID i czy bot został dodany do serwera. Kanały nie zostały założone."
            )
            return

        try:
            category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
            if category is None:
                category = await guild.create_category(CATEGORY_NAME)
                print(f"Założono kategorię „{CATEGORY_NAME}”.")

            await self.setup_ask_channel(guild, category)
            await self.setup_level_channels(guild, category)
        except discord.Forbidden:
            warn("Bot nie ma uprawnienia „Zarządzanie kanałami” na serwerze. Kanały nie zostały założone.")
        except discord.HTTPException as error:
            warn(f"Discord nie pozwolił założyć kanałów: {error}")

    async def ensure_channel(
        self, guild: discord.Guild, category: discord.CategoryChannel, saved_id: int | None,
        name: str, topic: str, greeting: str,
    ) -> discord.TextChannel:
        """Zwraca kanał: zapisany, istniejący o tej nazwie albo nowo założony (z powitaniem)."""
        if saved_id and (channel := guild.get_channel(saved_id)):
            return channel

        channel = discord.utils.get(category.text_channels, name=name)
        if channel is not None:
            print(f"Kanał #{name} już jest - zapisuję jego ID.")
            return channel

        channel = await guild.create_text_channel(name, category=category, topic=topic)
        await channel.send(greeting)
        print(f"Założono kanał #{name} i wysłano powitanie.")
        return channel

    async def setup_ask_channel(self, guild: discord.Guild, category: discord.CategoryChannel) -> None:
        state = read_json(KANALY_FILE, {})
        greeting = (
            "Cześć! Jestem Orion, pomocnik z fizyki do gry Misja Orion.\n"
            "Tutaj pytaj o wszystko z całej gry: zasady dynamiki Newtona, swobodne spadanie i opory ruchu.\n"
            f"{AI_NOTE}"
        )
        channel = await self.ensure_channel(
            guild, category, parse_channel_id(state.get(ASK_CHANNEL_NAME)),
            ASK_CHANNEL_NAME, "Pytania o fizykę z całej gry Misja Orion", greeting,
        )
        if state.get(ASK_CHANNEL_NAME) != str(channel.id):
            state[ASK_CHANNEL_NAME] = str(channel.id)
            write_json(KANALY_FILE, state)

    async def setup_level_channels(self, guild: discord.Guild, category: discord.CategoryChannel) -> None:
        levels = load_levels()
        for level in levels:
            saved_id = parse_channel_id(level.get("channel_id"))
            if saved_id:
                if guild.get_channel(saved_id) is None:
                    warn(
                        f"Kanał poziomu {level['numer']} (ID {saved_id}) nie istnieje. "
                        f"Wyczyść channel_id w {POZIOMY_FILE.name}, a bot założy go od nowa."
                    )
                continue

            topic = level_topic(level)
            about = f" Temat: {topic}." if topic else ""
            greeting = (
                f"Cześć! To kanał poziomu {level['numer']}: „{level['tytul']}”.{about}\n"
                "Pytaj tu o pojęcia, wzory i sytuacje z tego poziomu gry.\n"
                f"{AI_NOTE}"
            )
            channel = await self.ensure_channel(
                guild, category, None, level_channel_name(level),
                f"Poziom {level['numer']}: {level['tytul']}", greeting,
            )
            level["channel_id"] = str(channel.id)
            write_json(POZIOMY_FILE, levels)

    async def send_online_message(self) -> None:
        channel_id = self.settings.command_channel_id
        try:
            channel = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
            await channel.send(ONLINE_MESSAGE)
            print(f"Wysłano „{ONLINE_MESSAGE}” na kanał #{channel}.")
        except discord.NotFound:
            warn(f"Nie znaleziono kanału o ID {channel_id}. Sprawdź DISCORD_COMMAND_CHANNEL_ID.")
        except discord.Forbidden:
            warn(f"Bot nie ma uprawnień, żeby pisać na kanale o ID {channel_id}.")
        except discord.HTTPException as error:
            warn(f"Nie udało się wysłać wiadomości: {error}")


def main() -> None:
    # Polskie znaki w komunikatach także wtedy, gdy konsola Windows nie używa UTF-8.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    settings = load_settings()
    # Błędy w plikach JSON zgłaszamy przed logowaniem, a nie w trakcie działania bota.
    load_levels()
    if not isinstance(read_json(KANALY_FILE, {}), dict):
        fail(f"Plik {KANALY_FILE.name} powinien zawierać obiekt JSON, np. {{}}.")
    bot = Orion(settings)
    try:
        bot.run(settings.token)
    except discord.LoginFailure:
        fail("Discord odrzucił token. Sprawdź DISCORD_TOKEN w pliku .env (może wygasł albo został zresetowany).")
    except discord.PrivilegedIntentsRequired:
        fail("Bot potrzebuje uprawnień (intents), które nie są włączone w Discord Developer Portal.")
    except (discord.GatewayNotFound, OSError):
        fail("Nie udało się połączyć z Discordem. Sprawdź połączenie z internetem.")


if __name__ == "__main__":
    main()
