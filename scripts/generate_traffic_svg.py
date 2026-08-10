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
    return f"{value:,}".replace(",", " ")


def create_chart(
    points: list[Point],
    title: str,
    output: Path,
) -> None:
    if not points:
        return

    daily_points = points
    total_points = cumulative_points(points)

    # ─────────────────────────────────────────
    # Independent scales
    #
    # Daily values and cumulative values have
    # completely different ranges, therefore
    # each line gets its own Y scale.
    # ─────────────────────────────────────────

    daily_max = max(
        max(point.value for point in daily_points),
        1,
    )

    cumulative_max = max(
        max(point.value for point in total_points),
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

    daily_path = " ".join(
        f"{x(index):.1f},{y_daily(point.value):.1f}"
        for index, point in enumerate(daily_points)
    )

    cumulative_path = " ".join(
        f"{x(index):.1f},{y_cumulative(point.value):.1f}"
        for index, point in enumerate(total_points)
    )

    latest_daily = daily_points[-1]
    latest_cumulative = total_points[-1]

    last_x = x(len(points) - 1)

    daily_y = y_daily(latest_daily.value)
    cumulative_y = y_cumulative(latest_cumulative.value)

    # ─────────────────────────────────────────
    # Endpoint labels
    #
    # Important:
    # each value is positioned against the
    # endpoint of its OWN line.
    # ─────────────────────────────────────────

    label_gap = 5

    daily_label_y = daily_y - label_gap
    cumulative_label_y = cumulative_y + label_gap

    # Keep labels inside the chart viewport.
    daily_label_y = max(
        PADDING_TOP + 8,
        min(daily_label_y, HEIGHT - PADDING_BOTTOM),
    )

    cumulative_label_y = max(
        PADDING_TOP + 8,
        min(cumulative_label_y, HEIGHT - PADDING_BOTTOM),
    )

    # If the two endpoints are visually too close,
    # move the labels apart without changing the
    # actual line coordinates.
    minimum_label_distance = 12

    if abs(daily_label_y - cumulative_label_y) < minimum_label_distance:
        if daily_y <= cumulative_y:
            daily_label_y -= 6
            cumulative_label_y += 6
        else:
            daily_label_y += 6
            cumulative_label_y -= 6

    daily_label_y = max(
        PADDING_TOP + 8,
        min(daily_label_y, HEIGHT - PADDING_BOTTOM),
    )

    cumulative_label_y = max(
        PADDING_TOP + 8,
        min(cumulative_label_y, HEIGHT - PADDING_BOTTOM),
    )

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
      font-size: 10px;
      font-weight: 600;
      fill: #24292f;
    }}

    .label {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 8px;
      fill: #6e7781;
    }}

    .value {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 8px;
      font-weight: 600;
    }}

    .daily-line {{
      fill: none;
      stroke: #57606a;
      stroke-width: 1.5;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}

    .cumulative-line {{
      fill: none;
      stroke: #0969da;
      stroke-width: 1.5;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}

    .daily-point {{
      fill: #57606a;
    }}

    .cumulative-point {{
      fill: #0969da;
    }}

    .legend {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 7px;
      fill: #6e7781;
    }}
  </style>

  <!-- Title -->
  <text
    x="{PADDING_LEFT}"
    y="12"
    class="title"
  >{escape(title)}</text>

  <!-- Legend -->
  <line
    x1="{PADDING_LEFT}"
    y1="19"
    x2="{PADDING_LEFT + 9}"
    y2="19"
    class="daily-line"
  />

  <text
    x="{PADDING_LEFT + 12}"
    y="21.5"
    class="legend"
  >Daily</text>

  <line
    x1="{PADDING_LEFT + 47}"
    y1="19"
    x2="{PADDING_LEFT + 56}"
    y2="19"
    class="cumulative-line"
  />

  <text
    x="{PADDING_LEFT + 59}"
    y="21.5"
    class="legend"
  >Cumulative</text>

  <!-- Daily line -->
  <polyline
    points="{daily_path}"
    class="daily-line"
  />

  <!-- Cumulative line -->
  <polyline
    points="{cumulative_path}"
    class="cumulative-line"
  />

  <!-- Daily endpoint -->
  <circle
    cx="{last_x:.1f}"
    cy="{daily_y:.1f}"
    r="2"
    class="daily-point"
  />

  <text
    x="{last_x - 4:.1f}"
    y="{daily_label_y:.1f}"
    text-anchor="end"
    class="value"
    fill="#57606a"
  >{format_number(latest_daily.value)}</text>

  <!-- Cumulative endpoint -->
  <circle
    cx="{last_x:.1f}"
    cy="{cumulative_y:.1f}"
    r="2"
    class="cumulative-point"
  />

  <text
    x="{last_x - 4:.1f}"
    y="{cumulative_label_y:.1f}"
    text-anchor="end"
    class="value"
    fill="#0969da"
  >{format_number(latest_cumulative.value)}</text>

  <!-- Date range -->
  <text
    x="{PADDING_LEFT}"
    y="{HEIGHT - 8}"
    class="label"
  >{escape(points[0].date)}</text>

  <text
    x="{WIDTH - PADDING_RIGHT}"
    y="{HEIGHT - 8}"
    text-anchor="end"
    class="label"
  >{escape(points[-1].date)}</text>
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

    create_chart(
        clones,
        "GitHub clones",
        CHARTS / "clones.svg",
    )


if __name__ == "__main__":
    main()
