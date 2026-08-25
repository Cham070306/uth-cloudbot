import json
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data/sample/student_context.json"
TEMPLATE_START = date(2026, 8, 17)
TEMPLATE_END = date(2026, 8, 22)
CALENDAR_END = date(2026, 9, 30)


def expand_schedule_calendar():
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    templates = [
        item for item in data["schedules"]
        if TEMPLATE_START <= date.fromisoformat(item["date"]) <= TEMPLATE_END
    ]
    if len(templates) != 60:
        raise ValueError(f"Expected 60 base schedule templates, found {len(templates)}")

    schedules = [deepcopy(item) for item in templates]
    next_id = 61
    for template in templates:
        class_date = date.fromisoformat(template["date"]) + timedelta(days=7)
        while class_date <= CALENDAR_END:
            item = deepcopy(template)
            item["id"] = f"schedule-{next_id:03d}"
            item["date"] = class_date.isoformat()
            schedules.append(item)
            next_id += 1
            class_date += timedelta(days=7)

    data["schedules"] = schedules
    DATASET.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(schedules)


if __name__ == "__main__":
    print(f"Generated {expand_schedule_calendar()} schedule records")
