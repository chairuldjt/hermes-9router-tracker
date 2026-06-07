import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from http.cookiejar import CookieJar
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

BAR_WIDTH = 8
DEFAULT_LABEL_REPLACEMENTS = {
    "premium_interactions": "premium",
    "completions": "completion",
}
GENERIC_LABEL_PRIORITY = {
    "weekly": 1,
    "session": 2,
    "credit": 3,
    "chat": 4,
    "completion": 5,
    "premium": 6,
}
DEFAULT_PROVIDER_ICONS = {
    "antigravity": "🛸",
    "codex": "🧠",
    "gemini-cli": "💎",
    "github": "🐙",
    "kiro": "🪵",
    "qoder": "⚙️",
}


@dataclass
class TrackerConfig:
    base_url: str
    password: str
    timeout: float = 20.0
    page_size: int = 100
    provider_filter: str = ""


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _load_json_env(name: str, default: Any) -> Any:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def _provider_order_override() -> list[str]:
    raw = os.getenv("TRACKER_PROVIDER_ORDER", "").strip()
    if not raw:
        return []
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def _label_replacements() -> dict[str, str]:
    data = _load_json_env("TRACKER_LABEL_REPLACEMENTS", {})
    if not isinstance(data, dict):
        return dict(DEFAULT_LABEL_REPLACEMENTS)
    merged = dict(DEFAULT_LABEL_REPLACEMENTS)
    for key, value in data.items():
        merged[str(key)] = str(value)
    return merged


def _provider_label_order() -> dict[str, list[str]]:
    data = _load_json_env("TRACKER_PROVIDER_LABEL_ORDER", {})
    if not isinstance(data, dict):
        return {}
    normalized: dict[str, list[str]] = {}
    for provider, labels in data.items():
        if isinstance(labels, list):
            normalized[str(provider).lower()] = [str(label) for label in labels]
    return normalized


def _provider_icons() -> dict[str, str]:
    data = _load_json_env("TRACKER_PROVIDER_ICONS", {})
    if not isinstance(data, dict):
        return dict(DEFAULT_PROVIDER_ICONS)
    merged = dict(DEFAULT_PROVIDER_ICONS)
    for key, value in data.items():
        merged[str(key).lower()] = str(value)
    return merged


def _session():
    return build_opener(HTTPCookieProcessor(CookieJar()))


def _request_json(opener, method: str, url: str, payload: Any = None, query: dict[str, Any] | None = None) -> dict[str, Any]:
    if query:
        url = f"{url}?{urlencode(query)}"
    data = None
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method.upper())
    with opener.open(request, timeout=20) as response:
        body = response.read().decode("utf-8", errors="replace")
    return json.loads(body)


def _format_number(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        text = f"{value:.2f}"
        return text.rstrip("0").rstrip(".")
    if value in (None, ""):
        return "-"
    return str(value)


def _format_reset(value: Any) -> str:
    if not value:
        return "-"
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.strftime("%d %b %H:%M UTC")
    except Exception:
        return str(value)


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _remaining_percent(remaining: Any, total: Any) -> float | None:
    remaining_num = _safe_float(remaining)
    total_num = _safe_float(total)
    if remaining_num is None or total_num in (None, 0):
        return None
    return max(0.0, min(100.0, (remaining_num / total_num) * 100.0))


def _status_icon(percent_remaining: float | None) -> str:
    if percent_remaining is None:
        return "•"
    if percent_remaining <= 10:
        return "🔴"
    if percent_remaining <= 30:
        return "🟠"
    if percent_remaining <= 60:
        return "🟡"
    return "🟢"


def _progress_bar(percent_remaining: float | None) -> str:
    if percent_remaining is None:
        return "[" + ("·" * BAR_WIDTH) + "]"
    filled = round((percent_remaining / 100.0) * BAR_WIDTH)
    filled = max(0, min(BAR_WIDTH, filled))
    return "[" + ("█" * filled) + ("░" * (BAR_WIDTH - filled)) + "]"


def _provider_icon(provider: str) -> str:
    return _provider_icons().get(provider.lower(), "📦")


def _short_label(label: str) -> str:
    return _label_replacements().get(label, label)


def _label_sort_key(provider: str, label: str) -> tuple[int, str]:
    short = _short_label(label)
    provider_order = _provider_label_order().get(provider.lower())
    if provider_order:
        try:
            return (provider_order.index(short), short)
        except ValueError:
            pass
    return (GENERIC_LABEL_PRIORITY.get(short, 999), short.lower())


def _provider_sort_key(provider: str) -> tuple[int, str]:
    lowered = provider.lower()
    order = _provider_order_override()
    if order:
        try:
            return (order.index(lowered), lowered)
        except ValueError:
            pass
    return (999, lowered)


def _account_name(connection: dict[str, Any]) -> str:
    return (
        connection.get("displayName")
        or connection.get("accountLabel")
        or connection.get("email")
        or connection.get("name")
        or connection.get("id")
        or "unknown-account"
    )


def _normalize_quota_rows(provider: str, usage: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    quotas = usage.get("quotas") or {}
    for quota_name, quota_value in quotas.items():
        if not isinstance(quota_value, dict):
            continue
        label = quota_value.get("displayName") or quota_value.get("label") or quota_name
        remaining = quota_value.get("remaining")
        if remaining in (None, "") and quota_value.get("total") not in (None, "") and quota_value.get("used") not in (None, ""):
            try:
                remaining = float(quota_value["total"]) - float(quota_value["used"])
            except Exception:
                remaining = None
        extra = ""
        if quota_value.get("remainingPercentage") not in (None, ""):
            extra = f" ({_format_number(quota_value['remainingPercentage'])}%)"
        elif quota_value.get("unit"):
            extra = f" {quota_value['unit']}"
        rows.append(
            {
                "label": str(label),
                "used": _format_number(quota_value.get("used")),
                "total": "unlimited" if quota_value.get("unlimited") else _format_number(quota_value.get("total")),
                "remaining": _format_number(remaining),
                "reset": _format_reset(quota_value.get("resetAt")),
                "extra": extra,
                "remaining_percent": _remaining_percent(remaining, quota_value.get("total")),
            }
        )
    if not rows and usage.get("message"):
        rows.append(
            {
                "label": "message",
                "used": "-",
                "total": "-",
                "remaining": "-",
                "reset": "-",
                "extra": f" {usage['message']}",
                "remaining_percent": None,
            }
        )
    return rows


def _fetch_data(config: TrackerConfig) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    opener = _session()
    login = _request_json(opener, "POST", f"{config.base_url}/api/auth/login", {"password": config.password})
    if not login.get("success"):
        raise RuntimeError(login.get("error") or "login failed")
    params = {
        "page": 1,
        "pageSize": config.page_size,
        "accountStatus": "all",
        "sort": "priority",
    }
    if config.provider_filter and config.provider_filter != "all":
        params["provider"] = config.provider_filter
    payload = _request_json(opener, "GET", f"{config.base_url}/api/providers/client", query=params)
    connections = payload.get("connections") or []
    usages: dict[str, dict[str, Any]] = {}
    for connection in connections:
        try:
            usages[connection["id"]] = _request_json(opener, "GET", f"{config.base_url}/api/usage/{connection['id']}")
        except HTTPError as exc:
            usages[connection["id"]] = {"message": f"HTTP {exc.code}"}
        except Exception as exc:
            usages[connection["id"]] = {"message": str(exc)}
    return connections, usages


def _build_summary(connections: list[dict[str, Any]], usages: dict[str, dict[str, Any]]) -> list[str]:
    provider_counts: dict[str, int] = {}
    alerts: list[tuple[float, str]] = []
    for connection in connections:
        provider = str(connection.get("provider") or "unknown")
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        account = _account_name(connection)
        rows = _normalize_quota_rows(provider, usages.get(connection["id"], {}))
        for row in rows:
            remaining_pct = row.get("remaining_percent")
            if remaining_pct is None:
                continue
            if remaining_pct <= 30:
                label = _short_label(row["label"])
                alerts.append((remaining_pct, f"{provider} | {account} | {label} {row['remaining']}/{row['total']} ({remaining_pct:.0f}%)"))
    provider_summary = ", ".join(
        f"{name}:{provider_counts[name]}" for name in sorted(provider_counts.keys(), key=lambda item: _provider_sort_key(item))
    )
    lines = [
        "Summary",
        f"- account: {len(connections)}",
        f"- provider: {provider_summary}",
    ]
    if alerts:
        lines.append("- low quota:")
        for _pct, text in sorted(alerts, key=lambda item: item[0])[:8]:
            lines.append(f"  {text}")
    else:
        lines.append("- low quota: none")
    return lines


def scrape_quota(config: TrackerConfig, summary_only: bool = False) -> str:
    connections, usages = _fetch_data(config)
    lines = ["📊 AI Quota Tracker", f"Total account: {len(connections)}", ""]
    lines.extend(_build_summary(connections, usages))
    if summary_only:
        return "\n".join(lines).rstrip()
    lines.extend(["", "Detail", ""])
    grouped: dict[str, list[dict[str, Any]]] = {}
    for connection in connections:
        provider = str(connection.get("provider") or "unknown")
        grouped.setdefault(provider, []).append(connection)
    provider_names = sorted(grouped.keys(), key=lambda item: _provider_sort_key(item))
    global_index = 1
    for provider in provider_names:
        provider_connections = grouped[provider]
        lines.append(f"{_provider_icon(provider)} {provider.upper()} ({len(provider_connections)} account)")
        lines.append("")
        for connection in provider_connections:
            account = _account_name(connection)
            usage = usages.get(connection["id"], {})
            plan = usage.get("plan") or "-"
            card_title = provider.replace("-", " ").title()
            lines.append(f"{global_index}. {account}")
            rows = _normalize_quota_rows(provider, usage)
            lines.append(f"   {card_title} | plan {plan} | {len(rows)} quota")
            if not rows:
                lines.append("   • quota tidak tersedia")
                lines.append("")
                global_index += 1
                continue
            sorted_rows = sorted(rows, key=lambda row: _label_sort_key(provider, row["label"]))
            for row in sorted_rows:
                remaining_pct = row["remaining_percent"]
                icon = _status_icon(remaining_pct)
                bar = _progress_bar(remaining_pct)
                pct_text = f"{remaining_pct:.0f}%" if remaining_pct is not None else "-"
                label = _short_label(row["label"])
                lines.append(f"   {icon} {label}")
                lines.append(f"   {bar} {row['used']}/{row['total']} used | sisa {row['remaining']} ({pct_text})")
                lines.append(f"   reset {row['reset']}{row['extra']}")
            lines.append("")
            global_index += 1
    return "\n".join(lines).rstrip()


def scrape_quota_json(config: TrackerConfig) -> dict[str, Any]:
    connections, usages = _fetch_data(config)
    provider_names = sorted({str(c.get("provider") or "unknown") for c in connections}, key=lambda item: _provider_sort_key(item))
    return {
        "summary": {
            "accounts": len(connections),
            "providers": {provider: sum(1 for c in connections if str(c.get("provider") or "unknown") == provider) for provider in provider_names},
        },
        "connections": connections,
        "usages": usages,
    }


def _build_config(args: argparse.Namespace) -> TrackerConfig:
    base_url = (args.base_url or _env("AI_ITOPS_URL", "https://your-9router.example.com")).rstrip("/")
    password = args.password or _env("AI_ITOPS_PASSWORD", "")
    if not password:
        raise RuntimeError("missing password; pass --password or set AI_ITOPS_PASSWORD")
    timeout = float(args.timeout or _env("AI_ITOPS_TIMEOUT", "20"))
    page_size = int(args.page_size or _env("AI_ITOPS_PAGE_SIZE", "100"))
    provider_filter = (args.provider or _env("AI_ITOPS_PROVIDER", "")).strip().lower()
    return TrackerConfig(base_url=base_url, password=password, timeout=timeout, page_size=page_size, provider_filter=provider_filter)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Browserless quota tracker for 9Router-style dashboards")
    parser.add_argument("--base-url", help="Dashboard base URL")
    parser.add_argument("--password", help="Dashboard password")
    parser.add_argument("--provider", help="Optional provider filter, e.g. codex")
    parser.add_argument("--timeout", help="HTTP timeout in seconds")
    parser.add_argument("--page-size", help="Connection page size")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format")
    parser.add_argument("--summary-only", action="store_true", help="Return summary without detail section")
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = _parser().parse_args(argv)
    try:
        config = _build_config(args)
        if args.format == "json":
            print(json.dumps(scrape_quota_json(config), ensure_ascii=False, indent=2))
        else:
            print(scrape_quota(config, summary_only=args.summary_only))
        return 0
    except HTTPError as exc:
        print(f"Quota tracker failed: HTTP {exc.code}")
        return 1
    except Exception as exc:
        print(f"Quota tracker failed: {exc}")
        return 1
