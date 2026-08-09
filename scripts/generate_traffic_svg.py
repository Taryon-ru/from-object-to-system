
from __future__ import annotations

import json
import html
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "traffic" / "snapshots"
CHARTS = ROOT / "traffic" / "charts"

# ─────────────────────────────────────────────
# Компактные размеры (280×120)
# ─────────────────────────────────────────────
WIDTH = 280
HEIGHT = 120

PADDING_LEFT = 36      # место для цифр оси Y
PADDING_RIGHT = 10
PADDING_TOP = 22       # место для заголовка
PADDING_BOTTOM = 18    # место для дат

CHART_WIDTH = WIDTH - PADDING_LEFT - PADDING_RIGHT
CHART_HEIGHT = HEIGHT - PADDING_TOP - PADDING_BOTTOM


@dataclass(frozen=True)
class Point:
    date: str
    value: int


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
            points.append(Point(date=date, value=count))

    return sorted(points, key=lambda point: point.date)


def escape(value: str) -> str:
    return html.escape(value, quote=True)


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
      font: 600 12px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      fill: #1f2937;
    }}

    .label {{
      font: 400 10px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      fill: #6b7280;
    }}

    .grid {{
      stroke: #e5e7eb;
      stroke-width: 1;
    }}

    .line {{
      fill: none;
      stroke: #1f4b99;
      stroke-width: 2.5;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}

    .point {{
      fill: #1f4b99;
    }}

    @media (prefers-color-scheme: dark) {{
      .title {{
        fill: #f3f4f6;
      }}

      .label {{
        fill: #9ca3af;
      }}

      .grid {{
        stroke: #374151;
      }}

      .line {{
        stroke: #6ea8ff;
      }}

      .point {{
        fill: #6ea8ff;
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

  <line
    x1="{PADDING_LEFT}"
    y1="{PADDING_TOP + CHART_HEIGHT / 2}"
    x2="{WIDTH - PADDING_RIGHT}"
    y2="{PADDING_TOP + CHART_HEIGHT / 2}"
    class="grid"
  />

  <line
    x1="{PADDING_LEFT}"
    y1="{PADDING_TOP}"
    x2="{WIDTH - PADDING_RIGHT}"
    y2="{PADDING_TOP}"
    class="grid"
  />

  <polyline
    points="{line}"
    class="line"
  />

  <circle
    cx="{x(len(points) - 1):.1f}"
    cy="{y(latest.value):.1f}"
    r="4"
    class="point"
  />

  <text
    x="{PADDING_LEFT}"
    y="{HEIGHT - 12}"
    class="label"
  >{escape(points[0].date)}</text>

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
  >{latest.value:,}</text>
</svg>
"""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")


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
