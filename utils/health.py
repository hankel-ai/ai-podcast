"""Track source fetch health metrics over time."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

HEALTH_FILE = Path(__file__).parent.parent / "output" / "source_health.json"
MAX_HISTORY_DAYS = 30


def load_health() -> dict:
    """Load health data. Structure: {source_name: [entries]}."""
    if not HEALTH_FILE.exists():
        return {}
    try:
        with open(HEALTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load health data: {e}")
        return {}


def save_health(data: dict):
    try:
        HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HEALTH_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save health data: {e}")


def record_fetch(source_name: str, ok: bool, story_count: int, latency_ms: float, error: str = ""):
    """Record a single source fetch result."""
    data = load_health()
    entries = data.get(source_name, [])

    entries.append({
        "date": datetime.now().isoformat(),
        "ok": ok,
        "stories": story_count,
        "latency_ms": round(latency_ms),
        "error": error[:200] if error else "",
    })

    # Prune old entries
    cutoff = (datetime.now() - timedelta(days=MAX_HISTORY_DAYS)).isoformat()
    entries = [e for e in entries if e.get("date", "") >= cutoff]

    data[source_name] = entries
    save_health(data)


def get_source_stats(source_name: str, data: dict = None) -> dict:
    """Compute aggregate stats for a single source."""
    if data is None:
        data = load_health()
    entries = data.get(source_name, [])
    if not entries:
        return {"total": 0, "success_rate": 0, "avg_stories": 0, "avg_latency_ms": 0,
                "last_error": "", "status": "no data"}

    total = len(entries)
    successes = [e for e in entries if e.get("ok")]
    failures = [e for e in entries if not e.get("ok")]
    success_rate = len(successes) / total if total else 0

    avg_stories = sum(e.get("stories", 0) for e in successes) / len(successes) if successes else 0
    avg_latency = sum(e.get("latency_ms", 0) for e in entries) / total if total else 0

    last_error = ""
    last_error_date = ""
    if failures:
        last_fail = failures[-1]
        last_error = last_fail.get("error", "")
        last_error_date = last_fail.get("date", "")[:10]

    # Status classification
    recent = entries[-7:] if len(entries) >= 7 else entries
    recent_rate = sum(1 for e in recent if e.get("ok")) / len(recent)
    if recent_rate >= 0.85:
        status = "healthy"
    elif recent_rate >= 0.5:
        status = "degraded"
    else:
        status = "broken"

    return {
        "total": total,
        "successes": len(successes),
        "failures": len(failures),
        "success_rate": success_rate,
        "avg_stories": avg_stories,
        "avg_latency_ms": avg_latency,
        "last_error": last_error,
        "last_error_date": last_error_date,
        "status": status,
    }


def print_health_report():
    """Print a formatted health report for all sources."""
    data = load_health()
    if not data:
        print("No health data yet. Run the pipeline at least once first.")
        return

    status_icons = {"healthy": "+", "degraded": "~", "broken": "!", "no data": "?"}

    print(f"\n{'Source':<28} {'Status':<10} {'Rate':>6} {'Runs':>5} {'Avg Stories':>11} {'Avg ms':>7} {'Last Error'}")
    print("-" * 100)

    for source_name in sorted(data.keys()):
        stats = get_source_stats(source_name, data)
        icon = status_icons.get(stats["status"], "?")
        rate_str = f"{stats['success_rate']:.0%}"
        err_str = ""
        if stats["last_error"]:
            err_str = f"{stats['last_error_date']} {stats['last_error'][:30]}"

        print(
            f"[{icon}] {source_name:<25} {stats['status']:<10} {rate_str:>5} "
            f"{stats['total']:>5} {stats['avg_stories']:>10.1f} {stats['avg_latency_ms']:>7.0f} "
            f"{err_str}"
        )

    print()
    print("Legend: [+] healthy  [~] degraded  [!] broken  [?] no data")
    print(f"Data covers the last {MAX_HISTORY_DAYS} days.\n")
