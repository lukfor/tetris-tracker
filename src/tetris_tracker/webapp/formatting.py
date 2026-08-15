from datetime import datetime


def fmt_score(value):
    return "-" if value is None else "{:,}".format(value)


def fmt_duration(seconds):
    if seconds is None:
        return "-"

    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)

    if hours:
        return "{}:{:02d}:{:02d}".format(hours, minutes, secs)

    return "{}:{:02d}".format(minutes, secs)


def fmt_date(value):
    if not value:
        return "-"

    try:
        # Python 3.7 supports fromisoformat, but not a trailing Z.
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def tetris_rate(tetrises, lines):
    if not lines:
        return 0.0

    return (int(tetrises or 0) * 4.0 / int(lines)) * 100.0


def score_per_line(score, lines):
    if not lines:
        return 0.0

    return float(score or 0) / int(lines)
