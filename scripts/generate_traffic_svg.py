from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "traffic" / "snapshots"
CHARTS = ROOT / "traffic" / "charts"


# ─────────────────────────────────────────────
# Chart dimensions
# ─────────────────────────────────────────────

WIDTH = 280
HEIGHT = 120

PADDING_LEFT = 36
PADDING_RIGHT = 10
PADDING_TOP = 24
PADDING_BOTTOM = 22

CHART_WIDTH = WIDTH - PADDING_LEFT - PADDING_RIGHT
CHART_HEIGHT = HEIGHT - PADDING_TOP - PADDING_BOTTOM


# ─────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class Point:
    date: str
    value: int


# ─────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────

def load_snapshots(prefix: str) -> list[Point]:
    points: list[Point] = []

    for path in sorted(SNAPSHOTS.glob(f"{prefix}-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        if not isinstance(data, list):
            continue

        for item in data:
            if not isinstance(item, dict):
                continue

            timestamp = item.get("timestamp")
            count = item.get("count")

            if not isinstance(timestamp, str):
                continue

            if not isinstance(count, int):
                continue

            points.append(
                Point(
                    date=timestamp[:10],
                    value=count,
                )
            )

    return sorted(points, key=lambda point: point.date)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def escape(value: str) -> str:
    return html.escape(value, quote=True)


def format_number(value: int) -> str:
    return f"{value:,}"


def calculate_cumulative(points: list[Point]) -> list[Point]:
    cumulative: list[Point] = []
    total = 0

    for point in points:
        total += point.value

        cumulative.append(
            Point(
                date=point.date,
                value=total,
            )
        )

    return cumulative


# ─────────────────────────────────────────────
# SVG chart
# ─────────────────────────────────────────────

def create_clones_chart(
    points: list[Point],
    output: Path,
) -> None:
    if not points:
        return

    cumulative = calculate_cumulative(points)

    all_values = [
        point.value
        for point in points
    ] + [
        point.value
        for point in cumulative
    ]

    max_value = max(all_values)
    max_value = max(max_value, 1)

    x_step = (
        CHART_WIDTH / (len(points) - 1)
        if len(points) > 1
        else 0
    )

    def x(index: int) -> float:
        return PADDING_LEFT + index * x_step

    def y(value: int) -> float:
        return (
            PADDING_TOP
            + CHART_HEIGHT
            - (value / max_value) * CHART_HEIGHT
        )

    daily_path_points = [
        f"{x(index):.1f},{y(point.value):.1f}"
        for index, point in enumerate(points)
    ]

    cumulative_path_points = [
        f"{x(index):.1f},{y(point.value):.1f}"
        for index, point in enumerate(cumulative)
    ]

    daily_line = " ".join(daily_path_points)
    cumulative_line = " ".join(cumulative_path_points)

    latest_daily = points[-1]
    latest_cumulative = cumulative[-1]

    latest_x = x(len(points) - 1)
    latest_daily_y = y(latest_daily.value)
    latest_cumulative_y = y(latest_cumulative.value)

    # Prevent labels from going outside the SVG.
    daily_label_x = min(
        latest_x + 6,
        WIDTH - PADDING_RIGHT - 28,
    )

    cumulative_label_x = min(
        latest_x + 6,
        WIDTH - PADDING_RIGHT - 28,
    )

    # If both endpoints are close vertically,
    # move the daily label slightly upward.
    daily_label_y = latest_daily_y + 4
    cumulative_label_y = latest_cumulative_y + 4

    if abs(daily_label_y - cumulative_label_y) < 12:
        daily_label_y -= 7
        cumulative_label_y += 7

    latest_date = points[-1].date
    first_date = points[0].date

    svg = f"""\
<svg
  xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 {WIDTH} {HEIGHT}"
  width="{WIDTH}"
  height="{HEIGHT}"
  role="img"
  aria-label="GitHub clones"
>
  <style>
    .title {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 11px;
      font-weight: 600;
      fill: #333;
    }}

    .label {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 8px;
      fill: #888;
    }}

    .value {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 9px;
      font-weight: 600;
      fill: #333;
    }}

    .daily-line {{
      fill: none;
      stroke: #315a9b;
      stroke-width: 1.5;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}

    .cumulative-line {{
      fill: none;
      stroke: #777;
      stroke-width: 1.5;
      stroke-linecap: round;
      stroke-linejoin: round;
      stroke-dasharray: 4 3;
    }}

    .daily-point {{
      fill: #315a9b;
    }}

    .cumulative-point {{
      fill: #777;
    }}
  </style>

  <text
    x="{PADDING_LEFT}"
    y="16"
    class="title"
  >
    GitHub clones
  </text>

  <polyline
    points="{daily_line}"
    class="daily-line"
  />

  <polyline
    points="{cumulative_line}"
    class="cumulative-line"
  />

  <circle
    cx="{latest_x:.1f}"
    cy="{latest_daily_y:.1f}"
    r="2.5"
    class="daily-point"
  />

  <circle
    cx="{latest_x:.1f}"
    cy="{latest_cumulative_y:.1f}"
    r="2.5"
    class="cumulative-point"
  />

  <text
    x="{daily_label_x:.1f}"
    y="{daily_label_y:.1f}"
    class="value"
  >
    {format_number(latest_daily.value)}
  </text>

  <text
    x="{cumulative_label_x:.1f}"
    y="{cumulative_label_y:.1f}"
    class="value"
  >
    {format_number(latest_cumulative.value)}
  </text>

  <text
    x="{PADDING_LEFT}"
    y="{HEIGHT - 8}"
    class="label"
  >
    {escape(first_date)}
  </text>

  <text
    x="{WIDTH - PADDING_RIGHT}"
    y="{HEIGHT - 8}"
    text-anchor="end"
    class="label"
  >
    {escape(latest_date)}
  </text>
</svg>
"""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")


# ─────────────────────────────────────────────
# Generic single-line chart
# ─────────────────────────────────────────────

def create_chart(
    points: list[Point],
    title: str,
    output: Path,
) -> None:
    if not points:
        return

    max_value = max(point.value for point in points)
    max_value = max(max_value, 1)

    x_step = (
        CHART_WIDTH / (len(points) - 1)
        if len(points) > 1
        else 0
    )

    def x(index: int) -> float:
        return PADDING_LEFT + index * x_step

    def y(value: int) -> float:
        return (
            PADDING_TOP
            + CHART_HEIGHT
            - (value / max_value) * CHART_HEIGHT
        )

    path_points = [
        f"{x(index):.1f},{y(point.value):.1f}"
        for index, point in enumerate(points)
    ]

    line = " ".join(path_points)

    latest = points[-1]

    latest_x = x(len(points) - 1)
    latest_y = y(latest.value)

    label_x = min(
        latest_x + 6,
        WIDTH - PADDING_RIGHT - 28,
    )

    label_y = latest_y + 4

    svg = f"""\
<svg
  xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 {WIDTH} {HEIGHT}"
  width="{WIDTH}"
  height="{HEIGHT}"
  role="img"
  aria-label="{escape(title)}"
>
  <style>
    .title {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 11px;
      font-weight: 600;
      fill: #333;
    }}

    .label {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 8px;
      fill: #888;
    }}

    .value {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 9px;
      font-weight: 600;
      fill: #333;
    }}

    .line {{
      fill: none;
      stroke: #315a9b;
      stroke-width: 1.5;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}

    .point {{
      fill: #315a9b;
    }}
  </style>

  <text
    x="{PADDING_LEFT}"
    y="16"
    class="title"
  >
    {escape(title)}
  </text>

  <polyline
    points="{line}"
    class="line"
  />

  <circle
    cx="{latest_x:.1f}"
    cy="{latest_y:.1f}"
    r="2.5"
    class="point"
  />

  <text
    x="{label_x:.1f}"
    y="{label_y:.1f}"
    class="value"
  >
    {format_number(latest.value)}
  </text>

  <text
    x="{PADDING_LEFT}"
    y="{HEIGHT - 8}"
    class="label"
  >
    {escape(points[0].date)}
  </text>

  <text
    x="{WIDTH - PADDING_RIGHT}"
    y="{HEIGHT - 8}"
    text-anchor="end"
    class="label"
  >
    {escape(latest.date)}
  </text>
</svg>
"""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main() -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)

    views = load_snapshots("views")
    clones = load_snapshots("clones")

    create_chart(
        views,
        "GitHub views",
        CHARTS / "views.svg",
    )

    create_clones_chart(
        clones,
        CHARTS / "clones.svg",
    )


if __name__ == "__main__":
    main()
