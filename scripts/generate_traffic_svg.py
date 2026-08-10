from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "traffic" / "snapshots"
CHARTS = ROOT / "traffic" / "charts"


# ─────────────────────────────────────────────
# Chart size — НЕ МЕНЯЕМ
# ─────────────────────────────────────────────

WIDTH = 280
HEIGHT = 120

PADDING_LEFT = 36
PADDING_RIGHT = 36
PADDING_TOP = 24
PADDING_BOTTOM = 22

CHART_WIDTH = WIDTH - PADDING_LEFT - PADDING_RIGHT
CHART_HEIGHT = HEIGHT - PADDING_TOP - PADDING_BOTTOM


# ─────────────────────────────────────────────
# Visual configuration
# ─────────────────────────────────────────────

DAILY_COLOR = "#315f9f"
CUMULATIVE_COLOR = "#7b8794"

GRID_COLOR = "#d9dee5"
TEXT_COLOR = "#6b7280"
TITLE_COLOR = "#374151"

LINE_WIDTH = 1.8
CUMULATIVE_LINE_WIDTH = 1.5


@dataclass(frozen=True)
class Point:
    date: str
    value: int


@dataclass(frozen=True)
class ChartPoint:
    date: str
    daily: int
    cumulative: int


# ─────────────────────────────────────────────
# Data
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

            date = timestamp[:10]

            points.append(
                Point(
                    date=date,
                    value=count,
                )
            )

    return sorted(points, key=lambda point: point.date)


def build_clone_points(points: list[Point]) -> list[ChartPoint]:
    result: list[ChartPoint] = []

    cumulative = 0

    for point in points:
        cumulative += point.value

        result.append(
            ChartPoint(
                date=point.date,
                daily=point.value,
                cumulative=cumulative,
            )
        )

    return result


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def escape(value: str) -> str:
    return html.escape(value, quote=True)


def format_number(value: int) -> str:
    return f"{value:,}"


def create_y_scale(max_value: int) -> int:
    return max(max_value, 1)


# ─────────────────────────────────────────────
# Clones chart
# ─────────────────────────────────────────────

def create_clones_chart(
    points: list[ChartPoint],
    output: Path,
) -> None:
    if not points:
        return

    daily_max = create_y_scale(
        max(point.daily for point in points)
    )

    cumulative_max = create_y_scale(
        max(point.cumulative for point in points)
    )

    x_step = (
        CHART_WIDTH / (len(points) - 1)
        if len(points) > 1
        else 0
    )

    def x(index: int) -> float:
        return PADDING_LEFT + index * x_step

    def daily_y(value: int) -> float:
        return (
            PADDING_TOP
            + CHART_HEIGHT
            - (value / daily_max) * CHART_HEIGHT
        )

    def cumulative_y(value: int) -> float:
        return (
            PADDING_TOP
            + CHART_HEIGHT
            - (value / cumulative_max) * CHART_HEIGHT
        )

    daily_path = " ".join(
        f"{x(index):.1f},{daily_y(point.daily):.1f}"
        for index, point in enumerate(points)
    )

    cumulative_path = " ".join(
        f"{x(index):.1f},{cumulative_y(point.cumulative):.1f}"
        for index, point in enumerate(points)
    )

    latest = points[-1]

    latest_x = x(len(points) - 1)
    latest_daily_y = daily_y(latest.daily)
    latest_cumulative_y = cumulative_y(latest.cumulative)

    # Prevent endpoint labels from leaving the SVG.
    label_x = min(
        latest_x + 5,
        WIDTH - PADDING_RIGHT - 4,
    )

    # If the two labels are too close, separate them vertically.
    daily_label_y = latest_daily_y - 5
    cumulative_label_y = latest_cumulative_y + 11

    if abs(daily_label_y - cumulative_label_y) < 12:
        daily_label_y -= 6
        cumulative_label_y += 6

    daily_label_y = max(
        PADDING_TOP + 10,
        min(daily_label_y, HEIGHT - PADDING_BOTTOM),
    )

    cumulative_label_y = max(
        PADDING_TOP + 10,
        min(cumulative_label_y, HEIGHT - PADDING_BOTTOM),
    )

    first_date = points[0].date
    latest_date = latest.date

    svg = f"""\
<svg
  xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 {WIDTH} {HEIGHT}"
  width="{WIDTH}"
  height="{HEIGHT}"
  role="img"
  aria-label="GitHub clones: daily and cumulative"
>

  <style>
    .title {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 10px;
      font-weight: 600;
      fill: {TITLE_COLOR};
    }}

    .label {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 8px;
      fill: {TEXT_COLOR};
    }}

    .value-daily {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 8px;
      font-weight: 600;
      fill: {DAILY_COLOR};
    }}

    .value-cumulative {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 8px;
      font-weight: 600;
      fill: {CUMULATIVE_COLOR};
    }}

    .legend {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 7px;
      fill: {TEXT_COLOR};
    }}
  </style>

  <!-- Title -->

  <text
    x="{PADDING_LEFT}"
    y="10"
    class="title"
  >GitHub clones</text>


  <!-- Legend -->

  <line
    x1="{PADDING_LEFT}"
    y1="17"
    x2="{PADDING_LEFT + 9}"
    y2="17"
    stroke="{DAILY_COLOR}"
    stroke-width="2"
  />

  <text
    x="{PADDING_LEFT + 12}"
    y="19.5"
    class="legend"
  >daily</text>

  <line
    x1="{PADDING_LEFT + 52}"
    y1="17"
    x2="{PADDING_LEFT + 61}"
    y2="17"
    stroke="{CUMULATIVE_COLOR}"
    stroke-width="1.5"
  />

  <text
    x="{PADDING_LEFT + 64}"
    y="19.5"
    class="legend"
  >cumulative</text>


  <!-- Grid -->

  <line
    x1="{PADDING_LEFT}"
    y1="{PADDING_TOP + CHART_HEIGHT}"
    x2="{WIDTH - PADDING_RIGHT}"
    y2="{PADDING_TOP + CHART_HEIGHT}"
    stroke="{GRID_COLOR}"
    stroke-width="0.7"
  />


  <!-- Daily clones -->

  <polyline
    points="{daily_path}"
    fill="none"
    stroke="{DAILY_COLOR}"
    stroke-width="{LINE_WIDTH}"
    stroke-linecap="round"
    stroke-linejoin="round"
  />


  <!-- Cumulative clones -->

  <polyline
    points="{cumulative_path}"
    fill="none"
    stroke="{CUMULATIVE_COLOR}"
    stroke-width="{CUMULATIVE_LINE_WIDTH}"
    stroke-linecap="round"
    stroke-linejoin="round"
  />


  <!-- Latest daily point -->

  <circle
    cx="{latest_x:.1f}"
    cy="{latest_daily_y:.1f}"
    r="2"
    fill="{DAILY_COLOR}"
  />

  <text
    x="{label_x:.1f}"
    y="{daily_label_y:.1f}"
    class="value-daily"
  >{format_number(latest.daily)}</text>


  <!-- Latest cumulative point -->

  <circle
    cx="{latest_x:.1f}"
    cy="{latest_cumulative_y:.1f}"
    r="1.8"
    fill="{CUMULATIVE_COLOR}"
  />

  <text
    x="{label_x:.1f}"
    y="{cumulative_label_y:.1f}"
    class="value-cumulative"
  >{format_number(latest.cumulative)}</text>


  <!-- Dates -->

  <text
    x="{PADDING_LEFT}"
    y="{HEIGHT - 7}"
    class="label"
  >{escape(first_date)}</text>

  <text
    x="{WIDTH - PADDING_RIGHT}"
    y="{HEIGHT - 7}"
    text-anchor="end"
    class="label"
  >{escape(latest_date)}</text>

</svg>
"""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")


# ─────────────────────────────────────────────
# Views chart
# ─────────────────────────────────────────────

def create_views_chart(
    points: list[Point],
    output: Path,
) -> None:
    if not points:
        return

    max_value = create_y_scale(
        max(point.value for point in points)
    )

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

    path = " ".join(
        f"{x(index):.1f},{y(point.value):.1f}"
        for index, point in enumerate(points)
    )

    latest = points[-1]

    latest_x = x(len(points) - 1)
    latest_y = y(latest.value)

    label_x = min(
        latest_x + 5,
        WIDTH - PADDING_RIGHT - 4,
    )

    label_y = max(
        PADDING_TOP + 10,
        min(latest_y - 5, HEIGHT - PADDING_BOTTOM),
    )

    svg = f"""\
<svg
  xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 {WIDTH} {HEIGHT}"
  width="{WIDTH}"
  height="{HEIGHT}"
  role="img"
  aria-label="GitHub views"
>

  <style>
    .title {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 10px;
      font-weight: 600;
      fill: {TITLE_COLOR};
    }}

    .label {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 8px;
      fill: {TEXT_COLOR};
    }}

    .value {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 8px;
      font-weight: 600;
      fill: {DAILY_COLOR};
    }}
  </style>

  <text
    x="{PADDING_LEFT}"
    y="10"
    class="title"
  >GitHub views</text>


  <line
    x1="{PADDING_LEFT}"
    y1="{PADDING_TOP + CHART_HEIGHT}"
    x2="{WIDTH - PADDING_RIGHT}"
    y2="{PADDING_TOP + CHART_HEIGHT}"
    stroke="{GRID_COLOR}"
    stroke-width="0.7"
  />


  <polyline
    points="{path}"
    fill="none"
    stroke="{DAILY_COLOR}"
    stroke-width="{LINE_WIDTH}"
    stroke-linecap="round"
    stroke-linejoin="round"
  />


  <circle
    cx="{latest_x:.1f}"
    cy="{latest_y:.1f}"
    r="2"
    fill="{DAILY_COLOR}"
  />

  <text
    x="{label_x:.1f}"
    y="{label_y:.1f}"
    class="value"
  >{format_number(latest.value)}</text>


  <text
    x="{PADDING_LEFT}"
    y="{HEIGHT - 7}"
    class="label"
  >{escape(points[0].date)}</text>

  <text
    x="{WIDTH - PADDING_RIGHT}"
    y="{HEIGHT - 7}"
    text-anchor="end"
    class="label"
  >{escape(latest.date)}</text>

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

    create_views_chart(
        views,
        CHARTS / "views.svg",
    )

    clone_points = build_clone_points(clones)

    create_clones_chart(
        clone_points,
        CHARTS / "clones.svg",
    )


if __name__ == "__main__":
    main()
