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
PADDING_RIGHT = 36
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

            date = timestamp[:10]

            points.append(
                Point(
                    date=date,
                    value=count,
                )
            )

    # GitHub API returns hourly data in some responses.
    # Aggregate all records belonging to the same day.
    daily: dict[str, int] = {}

    for point in points:
        daily[point.date] = daily.get(point.date, 0) + point.value

    return [
        Point(date=date, value=value)
        for date, value in sorted(daily.items())
    ]


def cumulative_points(points: list[Point]) -> list[Point]:
    total = 0
    result: list[Point] = []

    for point in points:
        total += point.value

        result.append(
            Point(
                date=point.date,
                value=total,
            )
        )

    return result


# ─────────────────────────────────────────────
# SVG helpers
# ─────────────────────────────────────────────

def escape(value: str) -> str:
    return html.escape(value, quote=True)


def format_number(value: int) -> str:
    return f"{value:,}"


def build_polyline(
    points: list[Point],
    max_value: int,
    x_step: float,
) -> str:
    if not points:
        return ""

    def x(index: int) -> float:
        return PADDING_LEFT + index * x_step

    def y(value: int) -> float:
        return (
            PADDING_TOP
            + CHART_HEIGHT
            - (value / max_value) * CHART_HEIGHT
        )

    return " ".join(
        f"{x(index):.1f},{y(point.value):.1f}"
        for index, point in enumerate(points)
    )


# ─────────────────────────────────────────────
# Single-line chart
# ─────────────────────────────────────────────

def create_chart(
    points: list[Point],
    title: str,
    output: Path,
) -> None:
    if not points:
        return

    max_value = max(
        max(point.value for point in points),
        1,
    )

    x_step = (
        CHART_WIDTH / (len(points) - 1)
        if len(points) > 1
        else 0
    )

    line = build_polyline(
        points,
        max_value,
        x_step,
    )

    first = points[0]
    latest = points[-1]

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
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 11px;
      font-weight: 600;
      fill: #1f2937;
    }}

    .label {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 8px;
      fill: #6b7280;
    }}

    .grid {{
      stroke: #e5e7eb;
      stroke-width: 1;
    }}

    .line {{
      fill: none;
      stroke: #315f9f;
      stroke-width: 1.8;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}

    @media (prefers-color-scheme: dark) {{
      .title {{
        fill: #e5e7eb;
      }}

      .label {{
        fill: #9ca3af;
      }}

      .grid {{
        stroke: #374151;
      }}

      .line {{
        stroke: #8fb5e8;
      }}
    }}
  </style>

  <text
    x="{PADDING_LEFT}"
    y="22"
    class="title"
  >{escape(title)}</text>

  <line
    x1="{PADDING_LEFT}"
    y1="{PADDING_TOP + CHART_HEIGHT}"
    x2="{WIDTH - PADDING_RIGHT}"
    y2="{PADDING_TOP + CHART_HEIGHT}"
    class="grid"
  />

  <polyline
    points="{line}"
    class="line"
  />

  <text
    x="{PADDING_LEFT}"
    y="{HEIGHT - 12}"
    class="label"
  >{escape(first.date)}</text>

  <text
    x="{WIDTH - PADDING_RIGHT}"
    y="{HEIGHT - 12}"
    text-anchor="end"
    class="label"
  >{escape(latest.date)}</text>

  <text
    x="{WIDTH - PADDING_RIGHT}"
    y="{PADDING_TOP - 10}"
    text-anchor="end"
    class="label"
  >{format_number(latest.value)}</text>
</svg>
"""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")


# ─────────────────────────────────────────────
# Clones chart with cumulative series
# ─────────────────────────────────────────────

def create_clones_chart(
    points: list[Point],
    output: Path,
) -> None:
    if not points:
        return

    cumulative = cumulative_points(points)

    daily_max = max(
        max(point.value for point in points),
        1,
    )

    cumulative_max = max(
        max(point.value for point in cumulative),
        1,
    )

    x_step = (
        CHART_WIDTH / (len(points) - 1)
        if len(points) > 1
        else 0
    )

    def x(index: int) -> float:
        return PADDING_LEFT + index * x_step

    def y_daily(value: int) -> float:
        return (
            PADDING_TOP
            + CHART_HEIGHT
            - (value / daily_max) * CHART_HEIGHT
        )

    def y_cumulative(value: int) -> float:
        return (
            PADDING_TOP
            + CHART_HEIGHT
            - (value / cumulative_max) * CHART_HEIGHT
        )

    daily_line = " ".join(
        f"{x(index):.1f},{y_daily(point.value):.1f}"
        for index, point in enumerate(points)
    )

    cumulative_line = " ".join(
        f"{x(index):.1f},{y_cumulative(point.value):.1f}"
        for index, point in enumerate(cumulative)
    )

    first = points[0]
    latest = points[-1]
    latest_cumulative = cumulative[-1]

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
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 11px;
      font-weight: 600;
      fill: #1f2937;
    }}

    .legend {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 7px;
      fill: #6b7280;
    }}

    .label {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 8px;
      fill: #6b7280;
    }}

    .grid {{
      stroke: #e5e7eb;
      stroke-width: 1;
    }}

    .daily {{
      fill: none;
      stroke: #315f9f;
      stroke-width: 1.8;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}

    .cumulative {{
      fill: none;
      stroke: #9ca3af;
      stroke-width: 1.4;
      stroke-linecap: round;
      stroke-linejoin: round;
      stroke-dasharray: 3 2;
    }}

    @media (prefers-color-scheme: dark) {{
      .title {{
        fill: #e5e7eb;
      }}

      .legend,
      .label {{
        fill: #9ca3af;
      }}

      .grid {{
        stroke: #374151;
      }}

      .daily {{
        stroke: #8fb5e8;
      }}

      .cumulative {{
        stroke: #9ca3af;
      }}
    }}
  </style>

  <text
    x="{PADDING_LEFT}"
    y="12"
    class="title"
  >GitHub clones</text>

  <line
    x1="{PADDING_LEFT}"
    y1="{PADDING_TOP + CHART_HEIGHT}"
    x2="{WIDTH - PADDING_RIGHT}"
    y2="{PADDING_TOP + CHART_HEIGHT}"
    class="grid"
  />

  <line
    x1="{PADDING_LEFT}"
    y1="17"
    x2="{PADDING_LEFT + 10}"
    y2="17"
    class="daily"
  />

  <text
    x="{PADDING_LEFT + 13}"
    y="19"
    class="legend"
  >daily</text>

  <line
    x1="{PADDING_LEFT + 48}"
    y1="17"
    x2="{PADDING_LEFT + 58}"
    y2="17"
    class="cumulative"
  />

  <text
    x="{PADDING_LEFT + 61}"
    y="19"
    class="legend"
  >cumulative</text>

  <polyline
    points="{cumulative_line}"
    class="cumulative"
  />

  <polyline
    points="{daily_line}"
    class="daily"
  />

  <text
    x="{PADDING_LEFT}"
    y="{HEIGHT - 12}"
    class="label"
  >{escape(first.date)}</text>

  <text
    x="{WIDTH - PADDING_RIGHT}"
    y="{HEIGHT - 12}"
    text-anchor="end"
    class="label"
  >{escape(latest.date)}</text>

  <text
    x="{PADDING_LEFT - 4}"
    y="{PADDING_TOP + 7}"
    text-anchor="end"
    class="label"
  >{format_number(daily_max)}</text>

  <text
    x="{WIDTH - PADDING_RIGHT + 4}"
    y="{PADDING_TOP + 7}"
    class="label"
  >{format_number(cumulative_max)}</text>

  <text
    x="{WIDTH - PADDING_RIGHT}"
    y="{PADDING_TOP - 10}"
    text-anchor="end"
    class="label"
  >Σ {format_number(latest_cumulative.value)}</text>
</svg>
"""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main() -> None:
    CHARTS.mkdir(
        parents=True,
        exist_ok=True,
    )

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
