"""Bot Discord „Orion” - pomocnik z fizyki do gry Misja Orion."""

import sys
from dataclasses import dataclass
from pathlib import Path

import discord
from dotenv import dotenv_values

BOT_DIR = Path(__file__).resolve().parent
REPO_DIR = BOT_DIR.parent
ENV_FILE = REPO_DIR / ".env"

ONLINE_MESSAGE = "Orion online - pytaj o fizykę!"


@dataclass(frozen=True)
class Settings:
    token: str
    guild_id: int | None
    owner_id: int | None
    command_channel_id: int


def fail(message: str) -> None:
    """Wypisuje zrozumiały komunikat i kończy program."""
    print(f"BŁĄD: {message}", file=sys.stderr)
    sys.exit(1)


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
        guild_id=read_id(values, "DISCORD_GUILD_ID", required=False),
        owner_id=read_id(values, "DISCORD_OWNER_ID", required=False),
        command_channel_id=read_id(values, "DISCORD_COMMAND_CHANNEL_ID", required=True),
    )


class Orion(discord.Client):
    def __init__(self, settings: Settings) -> None:
        super().__init__(intents=discord.Intents.default())
        self.settings = settings
        self.announced = False

    async def on_ready(self) -> None:
        print(f"Zalogowano jako {self.user} (ID: {self.user.id}).")

        # on_ready wywołuje się też po każdym ponownym połączeniu - witamy się raz.
        if self.announced:
            return
        self.announced = True

        channel_id = self.settings.command_channel_id
        try:
            channel = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
            await channel.send(ONLINE_MESSAGE)
            print(f"Wysłano „{ONLINE_MESSAGE}” na kanał #{channel}.")
        except discord.NotFound:
            print(f"Nie znaleziono kanału o ID {channel_id}. Sprawdź DISCORD_COMMAND_CHANNEL_ID.", file=sys.stderr)
        except discord.Forbidden:
            print(f"Bot nie ma uprawnień, żeby pisać na kanale o ID {channel_id}.", file=sys.stderr)
        except discord.HTTPException as error:
            print(f"Nie udało się wysłać wiadomości: {error}", file=sys.stderr)


def main() -> None:
    # Polskie znaki w komunikatach także wtedy, gdy konsola Windows nie używa UTF-8.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    settings = load_settings()
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
