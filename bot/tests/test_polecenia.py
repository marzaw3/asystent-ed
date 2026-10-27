from polecenia import build_owner_input, owner_args, parse_command


def test_owner_args_are_exactly_as_agreed():
    assert owner_args() == [
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


def test_owner_args_have_no_model_and_no_session_resume():
    args = owner_args()
    for flag in ["--model", "--continue", "-c", "--resume", "-r"]:
        assert flag not in args


def test_owner_input_has_context_and_request():
    text = build_owner_input("  Dodaj poziom 7  ")
    assert "Orion" in text
    assert '"channel_id": ""' in text
    assert "<prosba_wlasciciela>\nDodaj poziom 7\n</prosba_wlasciciela>" in text


def test_commands_are_recognized():
    assert parse_command("!statystyki") == "statystyki"
    assert parse_command(" !PAUZA ") == "pauza"
    assert parse_command("!wznow") == "wznow"
    assert parse_command("!wznów") == "wznow"


def test_other_text_goes_to_claude():
    assert parse_command("Popraw definicję bezwładności") is None
    assert parse_command("!statystyki proszę") is None
