import argparse
from .hermes_config import (
    dump_yaml,
    ensure_dict,
    get_hermes_config_path,
    load_yaml,
    read_menu_commands,
    write_menu_commands,
)


def _default_command() -> str:
    return "router-quota-tracker"


def build_exec_command(command_name: str, provider: str = "") -> str:
    if provider:
        return f"{command_name} --provider {provider}"
    return command_name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install /quota quick command into Hermes")
    parser.add_argument("--hermes-bin", default="hermes", help="Hermes executable name or path")
    parser.add_argument("--command-name", default="quota", help="Slash command name to register")
    parser.add_argument("--runner", default=_default_command(), help="Executable Hermes should call, e.g. router-quota-tracker")
    parser.add_argument("--provider", default="", help="Optional provider filter for the installed command")
    parser.add_argument("--description", default="Check AI quota", help="Telegram menu description")
    parser.add_argument("--skip-telegram-menu", action="store_true", help="Do not register Telegram menu command")
    parser.add_argument("--restart-gateway", action="store_true", help="Restart Hermes gateway after install")
    args = parser.parse_args(argv)

    config_path = get_hermes_config_path(args.hermes_bin)
    data = load_yaml(config_path)
    quick_commands = ensure_dict(data, "quick_commands")
    quick_commands[args.command_name] = {
        "type": "exec",
        "command": build_exec_command(args.runner, args.provider),
    }

    if not args.skip_telegram_menu:
        telegram_cfg = ensure_dict(data, "telegram")
        menu = read_menu_commands(telegram_cfg)
        menu[args.command_name] = args.description
        write_menu_commands(telegram_cfg, menu)

    dump_yaml(config_path, data)
    print(f"Installed /{args.command_name} in {config_path}")
    if args.restart_gateway:
        import subprocess
        subprocess.run([args.hermes_bin, "gateway", "restart"], check=True)
        print("Hermes gateway restarted.")
    else:
        print("Next step: run 'hermes gateway restart' so Telegram picks up the menu change.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
