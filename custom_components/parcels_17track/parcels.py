"""Pure parcel logic: normalising, sorting, counting, diffing and message texts.

This module deliberately has no Home Assistant imports so it can be unit tested
on its own.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, Iterable, List, Optional

STATE_ALERT = "alert"
STATE_UNDELIVERED = "undelivered"
STATE_EXPIRED = "expired"
STATE_OUT_FOR_DELIVERY = "out_for_delivery"
STATE_READY = "ready_to_be_picked_up"
STATE_IN_TRANSIT = "in_transit"
STATE_NOT_FOUND = "not_found"
STATE_DELIVERED = "delivered"

PROBLEM_STATES = frozenset({STATE_ALERT, STATE_UNDELIVERED, STATE_EXPIRED})
TRANSIT_STATES = frozenset({STATE_IN_TRANSIT, STATE_OUT_FOR_DELIVERY, STATE_NOT_FOUND})

# Display / sort priority: things that need attention first, delivered last.
ORDER: List[str] = [
    STATE_ALERT,
    STATE_UNDELIVERED,
    STATE_EXPIRED,
    STATE_OUT_FOR_DELIVERY,
    STATE_READY,
    STATE_IN_TRANSIT,
    STATE_NOT_FOUND,
    STATE_DELIVERED,
]

LABELS: Dict[str, Dict[str, str]] = {
    "en": {
        STATE_ALERT: "Problem",
        STATE_UNDELIVERED: "Delivery failed",
        STATE_EXPIRED: "Expired",
        STATE_OUT_FOR_DELIVERY: "Out for delivery",
        STATE_READY: "Ready for pickup",
        STATE_IN_TRANSIT: "In transit",
        STATE_NOT_FOUND: "No data yet",
        STATE_DELIVERED: "Delivered",
        "new": "New parcel",
        "updated": "Status updated",
    },
    "de": {
        STATE_ALERT: "Problem",
        STATE_UNDELIVERED: "Zustellung fehlgeschlagen",
        STATE_EXPIRED: "Abgelaufen",
        STATE_OUT_FOR_DELIVERY: "Heute in Zustellung",
        STATE_READY: "Abholbereit",
        STATE_IN_TRANSIT: "Unterwegs",
        STATE_NOT_FOUND: "Noch keine Daten",
        STATE_DELIVERED: "Zugestellt",
        "new": "Neues Paket",
        "updated": "Status aktualisiert",
    },
}

EMOJI: Dict[str, str] = {
    "new": "📦",
    "in_transit": "🚚",
    "out_for_delivery": "🚚",
    "ready_for_pickup": "🏪",
    "delivered": "✅",
    "problem": "⚠️",
}


def status_key(status: Optional[str]) -> str:
    """Turn a 17TRACK status ("Ready to be Picked Up") into a key."""
    key = re.sub(r"[^a-z0-9]+", "_", (status or "").lower()).strip("_")
    return key or STATE_NOT_FOUND


def parse_keywords(text: Optional[str]) -> List[str]:
    """Split the comma/newline separated keyword option."""
    return [k.strip().lower() for k in re.split(r"[,\n]", text or "") if k.strip()]


def language(lang: Optional[str]) -> str:
    """Map a Home Assistant language to one we have texts for."""
    return "de" if (lang or "").lower().startswith("de") else "en"


def normalize(raw: Dict[str, Any], keywords: Iterable[str], lang: str = "en") -> Dict[str, Any]:
    """Normalise one package dict from seventeentrack.get_packages."""
    number = str(raw.get("tracking_number") or "").strip()
    state = status_key(raw.get("status"))
    info = raw.get("info_text") or None
    if state == STATE_IN_TRANSIT and info:
        low = info.lower()
        if any(k in low for k in keywords):
            state = STATE_OUT_FOR_DELIVERY
    return {
        "tracking_number": number,
        "name": raw.get("friendly_name") or number,
        "friendly_name": raw.get("friendly_name") or None,
        "status": raw.get("status"),
        "state": state,
        "info_text": info,
        "location": raw.get("location") or None,
        "timestamp": raw.get("timestamp"),
        "origin_country": raw.get("origin_country") or None,
        "destination_country": raw.get("destination_country") or None,
        "package_type": raw.get("package_type") or None,
        "url": f"https://t.17track.net/{language(lang)}#nums={number}",
    }


def parse_ts(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO timestamp; naive values are treated as UTC."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def sort_parcels(parcels: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort by priority, newest event first within the same state."""

    def key(p: Dict[str, Any]):
        state = p["state"]
        rank = ORDER.index(state) if state in ORDER else ORDER.index(STATE_NOT_FOUND)
        ts = parse_ts(p.get("timestamp"))
        return (rank, -(ts.timestamp() if ts else 0.0))

    return sorted(parcels, key=key)


def counts(parcels: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    """Count parcels per group."""
    plist = list(parcels)
    states = [p["state"] for p in plist]
    delivered = states.count(STATE_DELIVERED)
    return {
        "total": len(plist),
        "open": len(plist) - delivered,
        "in_transit": sum(s in TRANSIT_STATES for s in states),
        "out_for_delivery": states.count(STATE_OUT_FOR_DELIVERY),
        "ready_for_pickup": states.count(STATE_READY),
        "delivered": delivered,
        "problems": sum(s in PROBLEM_STATES for s in states),
    }


def snapshot(parcels: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Minimal persisted state used to detect changes across refreshes/restarts."""
    return {p["tracking_number"]: {"state": p["state"], "info_text": p.get("info_text")} for p in parcels}


def event_for_state(state: str) -> Optional[str]:
    """Which notification event a newly reached state represents."""
    if state in PROBLEM_STATES:
        return "problem"
    return {
        STATE_IN_TRANSIT: "in_transit",
        STATE_OUT_FOR_DELIVERY: "out_for_delivery",
        STATE_READY: "ready_for_pickup",
        STATE_DELIVERED: "delivered",
    }.get(state)


def diff(old: Optional[Dict[str, Dict[str, Any]]], parcels: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Changes between the previous snapshot and the new parcel list.

    Returns nothing when there is no previous snapshot (first run), so a fresh
    install does not announce every existing parcel.
    """
    if old is None:
        return []
    changes: List[Dict[str, Any]] = []
    for p in parcels:
        prev = old.get(p["tracking_number"])
        if prev is None:
            changes.append({"type": "new", "parcel": p, "previous_state": None})
            continue
        if prev.get("state") != p["state"]:
            event = event_for_state(p["state"])
            if event:
                changes.append({"type": event, "parcel": p, "previous_state": prev.get("state")})
    return changes


def archive_candidates(parcels: Iterable[Dict[str, Any]], days: int, now: datetime) -> List[str]:
    """Tracking numbers of parcels delivered at least `days` days ago."""
    if days <= 0:
        return []
    limit = now - timedelta(days=days)
    out = []
    for p in parcels:
        ts = parse_ts(p.get("timestamp"))
        if p["state"] == STATE_DELIVERED and ts is not None and ts <= limit:
            out.append(p["tracking_number"])
    return out


def message(change: Dict[str, Any], lang: str) -> Dict[str, str]:
    """Title/message for a push notification."""
    texts = LABELS[language(lang)]
    p = change["parcel"]
    event = change["type"]
    label = texts.get(p["state"], p.get("status") or "")
    details = " · ".join(x for x in (p.get("info_text"), p.get("location")) if x)
    if event == "new":
        title = f"{EMOJI['new']} {texts['new']}: {p['name']}"
        body = f"{label} – {details}" if details else label
    else:
        title = f"{EMOJI.get(event, '📦')} {p['name']}: {label}"
        body = details or texts["updated"]
    return {"title": title, "message": body}
