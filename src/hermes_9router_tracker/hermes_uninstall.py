import argparse
import subprocess
from .hermes_config import (
    dump_yaml,
    ensure_dict,
    get_hermes_config_path,
    load_yaml,
    read_menu_commands,
    write_menu_commands,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Uninstall a quota quick command from Hermes")
    parser.add_argument("--hermes-bin", default="hermes", help="Hermes executable name or path")
    parser.add_argument("--command-name", default="quota", help="Slash command name to remove")
    parser.add_argument("--restart-gateway", action="store_true", help="Restart Hermes gateway after uninstall")
    args = parser.parse_args(argv)

    config_path = get_hermes_config_path(args.hermes_bin)
    data = load_yaml(config_path)

    quick_commands = ensure_dict(data, "quick_commands")
    quick_commands.pop(args.command_name, None)

    telegram_cfg = ensure_dict(data, "telegram")
    menu = read_menu_commands(telegram_cfg)
    menu.pop(args.command_name, None)
    write_menu_commands(telegram_cfg, menu)

    dump_yaml(config_path, data)
    print(f"Removed /{args.command_name} from {config_path}")
    if args.restart_gateway:
        subprocess.run([args.hermes_bin, "gateway", "restart"], check=True)
        print("Hermes gateway restarted.")
    else:
        print("Next step: run 'hermes gateway restart' so Telegram removes the menu entry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
