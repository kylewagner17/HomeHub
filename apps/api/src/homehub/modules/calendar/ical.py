"""Minimal iCalendar VEVENT parse/serialize for M6 import/export."""

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta


@dataclass
class ParsedIcalEvent:
    uid: str | None
    title: str
    description: str | None
    location: str | None
    starts_at: datetime
    ends_at: datetime
    all_day: bool


def _unfold_lines(text: str) -> list[str]:
    raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines: list[str] = []
    for line in raw:
        if line.startswith((" ", "\t")) and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def _parse_ical_datetime(value: str, tz_name: str | None) -> tuple[datetime, bool]:
    value = value.strip()
    if len(value) == 8 and value.isdigit():
        d = date(int(value[0:4]), int(value[4:6]), int(value[6:8]))
        start = datetime(d.year, d.month, d.day, tzinfo=UTC)
        return start, True
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    if "T" in value and len(value) >= 15:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None and tz_name:
            dt = dt.replace(tzinfo=UTC)
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt, False
    raise ValueError(f"Unsupported iCal datetime: {value}")


def _split_prop(line: str) -> tuple[str, dict[str, str], str]:
    if ":" not in line:
        raise ValueError(f"Invalid iCal line: {line}")
    head, body = line.split(":", 1)
    parts = head.split(";")
    name = parts[0].upper()
    params: dict[str, str] = {}
    for part in parts[1:]:
        if "=" in part:
            k, v = part.split("=", 1)
            params[k.upper()] = v
    return name, params, body


def parse_ics_events(ics_text: str) -> list[ParsedIcalEvent]:
    """Extract VEVENT components from ICS text."""
    lines = _unfold_lines(ics_text)
    events: list[ParsedIcalEvent] = []
    in_event = False
    uid: str | None = None
    title = "Untitled"
    description: str | None = None
    location: str | None = None
    dtstart: datetime | None = None
    dtend: datetime | None = None
    all_day = False
    dtstart_tz: str | None = None

    for line in lines:
        upper = line.upper()
        if upper == "BEGIN:VEVENT":
            in_event = True
            uid = None
            title = "Untitled"
            description = None
            location = None
            dtstart = None
            dtend = None
            all_day = False
            dtstart_tz = None
            continue
        if upper == "END:VEVENT":
            if in_event and dtstart is not None:
                end = dtend if dtend is not None else dtstart + timedelta(hours=1)
                events.append(
                    ParsedIcalEvent(
                        uid=uid,
                        title=title.strip() or "Untitled",
                        description=description,
                        location=location,
                        starts_at=dtstart,
                        ends_at=end,
                        all_day=all_day,
                    )
                )
            in_event = False
            continue
        if not in_event:
            continue
        name, params, body = _split_prop(line)
        if name == "UID":
            uid = body.strip()
        elif name == "SUMMARY":
            title = body.strip()
        elif name == "DESCRIPTION":
            description = body.strip()
        elif name == "LOCATION":
            location = body.strip()
        elif name == "DTSTART":
            dtstart_tz = params.get("TZID")
            dtstart, all_day = _parse_ical_datetime(body, dtstart_tz)
        elif name == "DTEND":
            dtend, _ = _parse_ical_datetime(body, params.get("TZID") or dtstart_tz)

    return events


def _format_ical_dt(dt: datetime, all_day: bool) -> str:
    if all_day:
        d = dt.astimezone(UTC)
        return d.strftime("%Y%m%d")
    utc = dt.astimezone(UTC)
    return utc.strftime("%Y%m%dT%H%M%SZ")


def serialize_events_to_ics(events: list[ParsedIcalEvent]) -> str:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HomeHub//Calendar//EN"]
    for idx, ev in enumerate(events):
        uid = ev.uid or f"homehub-{idx}@local"
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"SUMMARY:{_escape_ical(ev.title)}",
                f"DTSTART:{_format_ical_dt(ev.starts_at, ev.all_day)}",
                f"DTEND:{_format_ical_dt(ev.ends_at, ev.all_day)}",
            ]
        )
        if ev.description:
            lines.append(f"DESCRIPTION:{_escape_ical(ev.description)}")
        if ev.location:
            lines.append(f"LOCATION:{_escape_ical(ev.location)}")
        lines.extend(["END:VEVENT"])
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def _escape_ical(value: str) -> str:
    return re.sub(r"([\\;,])", r"\\\1", value.replace("\n", "\\n"))
