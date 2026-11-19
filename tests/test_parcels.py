"""Unit tests for the Home Assistant independent parcel logic."""

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path

# Load parcels.py directly so the package __init__ (which needs Home Assistant) isn't imported.
_PATH = Path(__file__).parents[1] / "custom_components" / "parcels_17track" / "parcels.py"
_spec = importlib.util.spec_from_file_location("parcels", _PATH)
pl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pl)

KW = pl.parse_keywords("out for delivery, In Zustellung")
NOW = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)


def raw(num, status, info="", ts=None, name=None, loc=""):
    return {"tracking_number": num, "status": status, "info_text": info, "timestamp": ts, "friendly_name": name, "location": loc}


def test_status_key():
    assert pl.status_key("Ready to be Picked Up") == "ready_to_be_picked_up"
    assert pl.status_key("In Transit") == "in_transit"
    assert pl.status_key(None) == "not_found"


def test_keywords():
    assert KW == ["out for delivery", "in zustellung"]
    assert pl.parse_keywords("a,\n b ,,") == ["a", "b"]


def test_normalize_out_for_delivery_and_url():
    p = pl.normalize(raw("JJD1", "In Transit", "Die Sendung ist in Zustellung"), KW, "de")
    assert p["state"] == "out_for_delivery"
    assert p["name"] == "JJD1"
    assert p["url"] == "https://t.17track.net/de#nums=JJD1"
    q = pl.normalize(raw("X", "In Transit", "Sorted in hub", name="Shoes"), KW)
    assert q["state"] == "in_transit" and q["name"] == "Shoes"


def test_sort_priority_and_time():
    ps = [
        pl.normalize(raw("D", "Delivered", ts="2026-11-18T10:00:00+00:00"), KW),
        pl.normalize(raw("T1", "In Transit", ts="2026-11-17T10:00:00+00:00"), KW),
        pl.normalize(raw("T2", "In Transit", ts="2026-11-19T10:00:00+00:00"), KW),
        pl.normalize(raw("A", "Alert"), KW),
        pl.normalize(raw("R", "Ready to be Picked Up"), KW),
        pl.normalize(raw("O", "In Transit", "out for delivery"), KW),
    ]
    assert [p["tracking_number"] for p in pl.sort_parcels(ps)] == ["A", "O", "R", "T2", "T1", "D"]


def test_counts():
    ps = [pl.normalize(raw(n, s, i), KW) for n, s, i in [
        ("1", "In Transit", ""), ("2", "In Transit", "out for delivery"), ("3", "Not Found", ""),
        ("4", "Delivered", ""), ("5", "Undelivered", ""), ("6", "Ready to be Picked Up", "")]]
    c = pl.counts(ps)
    assert c == {"total": 6, "open": 5, "in_transit": 3, "out_for_delivery": 1,
                 "ready_for_pickup": 1, "delivered": 1, "problems": 1}


def test_diff_first_run_is_silent():
    ps = [pl.normalize(raw("1", "In Transit"), KW)]
    assert pl.diff(None, ps) == []


def test_diff_new_and_changes():
    old = pl.snapshot([
        pl.normalize(raw("A", "In Transit"), KW),
        pl.normalize(raw("B", "In Transit"), KW),
        pl.normalize(raw("C", "Ready to be Picked Up"), KW),
        pl.normalize(raw("E", "Not Found"), KW),
    ])
    new = [
        pl.normalize(raw("A", "In Transit", "out for delivery"), KW),
        pl.normalize(raw("B", "Delivered"), KW),
        pl.normalize(raw("C", "Ready to be Picked Up"), KW),
        pl.normalize(raw("D", "Not Found"), KW),
        pl.normalize(raw("E", "Alert"), KW),
    ]
    got = {(c["type"], c["parcel"]["tracking_number"]) for c in pl.diff(old, new)}
    assert got == {("out_for_delivery", "A"), ("delivered", "B"), ("new", "D"), ("problem", "E")}


def test_archive_candidates():
    ps = [
        pl.normalize(raw("old", "Delivered", ts=(NOW - timedelta(days=4)).isoformat()), KW),
        pl.normalize(raw("new", "Delivered", ts=(NOW - timedelta(days=1)).isoformat()), KW),
        pl.normalize(raw("naive", "Delivered", ts="2026-11-01T08:00:00"), KW),
        pl.normalize(raw("nots", "Delivered"), KW),
        pl.normalize(raw("transit", "In Transit", ts=(NOW - timedelta(days=9)).isoformat()), KW),
    ]
    assert pl.archive_candidates(ps, 3, NOW) == ["old", "naive"]
    assert pl.archive_candidates(ps, 0, NOW) == []


def test_messages():
    p = pl.normalize(raw("A", "In Transit", "Die Sendung ist in Zustellung", name="Kopfhörer", loc="Frankfurt"), KW, "de")
    m = pl.message({"type": "out_for_delivery", "parcel": p}, "de")
    assert m == {"title": "🚚 Kopfhörer: Heute in Zustellung", "message": "Die Sendung ist in Zustellung · Frankfurt"}
    n = pl.message({"type": "new", "parcel": pl.normalize(raw("B", "Not Found"), KW)}, "en")
    assert n == {"title": "📦 New parcel: B", "message": "No data yet"}
