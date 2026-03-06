import math
from datetime import time, datetime, timedelta

from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import ClassSession


# Fixed weekday ordering used by the timetable grid in the frontend.
DAYS = [(1, "Mon"), (2, "Tue"), (3, "Wed"), (4, "Thu"), (5, "Fri"), (6, "Sat"), (7, "Sun")]


# Generate timetable slots in fixed intervals so sessions
# can be placed into a predictable grid structure.
def _time_range(start: time, end: time, step_minutes: int = 30):
    dt = datetime.combine(datetime.today(), start)
    dt_end = datetime.combine(datetime.today(), end)
    step = timedelta(minutes=step_minutes)
    while dt < dt_end:
        yield dt.time()
        dt += step


def _fmt(t: time) -> str:
    return t.strftime("%H:%M")


# Build a frontend-friendly timetable matrix.
# Each starting slot may contain a rowspan so long sessions
# render once and later occupied cells can be skipped.
@api_view(["GET"])
def dashboard_api(request):
    day_start = time(8, 0)
    day_end = time(19, 30)
    step = 30

    sessions = (
        ClassSession.objects.filter(course__user=request.user)
        .select_related("course")
        .order_by("day_of_week", "start_time")
    )

    slots = list(_time_range(day_start, day_end, step_minutes=step))
    slot_labels = [_fmt(t) for t in slots]
    grid = {label: {d: None for d, _ in DAYS} for label in slot_labels}

    for s in sessions:
        start_label = _fmt(s.start_time)
        start_dt = datetime.combine(datetime.today(), s.start_time)
        end_dt = datetime.combine(datetime.today(), s.end_time)
        minutes = int((end_dt - start_dt).total_seconds() // 60)
        span = max(1, math.ceil(minutes / step))

        title = s.course.course_name
        subtitle = s.location or ""

        if start_label in grid:
            grid[start_label][s.day_of_week] = {
                "title": title,
                "subtitle": subtitle,
                "rowspan": span,
                "session_id": s.id
            }

            dt = start_dt + timedelta(minutes=step)
            for _ in range(span - 1):
                label = _fmt(dt.time())
                if label in grid:
                    grid[label][s.day_of_week] = {"skip": True}
                dt += timedelta(minutes=step)

    rows = []
    for label in slot_labels:
        row_cells = [grid[label][d] for d, _ in DAYS]
        rows.append([label, row_cells])

    return Response({"days": DAYS, "rows": rows})