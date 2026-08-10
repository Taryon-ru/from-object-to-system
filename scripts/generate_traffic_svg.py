from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

SNAPSHOTS = ROOT / "traffic" / "snapshots"
CHARTS = ROOT / "traffic" / "charts"


# ============================================================
# Размеры SVG
#
# Размер намеренно НЕ меняем.
# График используется непосредственно в README GitHub.
# ============================================================

WIDTH = 280
HEIGHT = 120


# ============================================================
# Геометрия графика
# ============================================================

PADDING_LEFT = 36

# Справа оставляем дополнительное место.
#
# Раньше конечная точка практически совпадала с правой
# границей области построения, поэтому подпись значения
# приходилось ставить слева от точки — прямо поверх линии.
#
# Теперь справа резервируется место под конечные значения.
PADDING_RIGHT = 42

PADDING_TOP = 24
PADDING_BOTTOM = 22


CHART_WIDTH = WIDTH - PADDING_LEFT - PADDING_RIGHT
CHART_HEIGHT = HEIGHT - PADDING_TOP - PADDING_BOTTOM


# ============================================================
# Цвета
#
# Цвета намеренно спокойные.
# SVG используется как небольшая информационная карточка,
# поэтому здесь нет яркой декоративной палитры.
# ============================================================

COLOR_DAILY = "#2563eb"
COLOR_TOTAL = "#64748b"

COLOR_TEXT = "#475569"
COLOR_MUTED = "#94a3b8"

COLOR_GRID = "#e2e8f0"


# ============================================================
# Данные
# ============================================================

@dataclass(frozen=True)
class Point:
    date: str
    value: int


# ============================================================
# Загрузка snapshot-файлов
# ============================================================

def load_snapshots(prefix: str) -> list[Point]:
    """
    Загружает дневные значения из snapshot-файлов.

    Ожидаемый формат файла:

    [
        {
            "timestamp": "2026-08-10T00:00:00Z",
            "count": 42
        }
    ]

    GitHub Traffic API возвращает массив дневных значений.
    """

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

    # На случай, если GitHub API или snapshot-файлы содержат
    # несколько записей для одной даты.
    #
    # Последнее значение считается актуальным.
    by_date: dict[str, Point] = {}

    for point in points:
        by_date[point.date] = point

    return sorted(
        by_date.values(),
        key=lambda point: point.date,
    )


# ============================================================
# Вспомогательные функции
# ============================================================

def escape(value: str) -> str:
    """Безопасное экранирование текста для SVG."""

    return html.escape(value, quote=True)


def format_number(value: int) -> str:
    """
    Форматирование числа для SVG.

    Используется неразрывный пробел (U+00A0) в качестве
    разделителя разрядов — соответствует ISO 80000-1 и ГОСТ.

    Например:
        1234 -> "1 234"
        128  -> "128"
    """
    return f"{value:,}".replace(",", "\u00a0")


# ============================================================
# Масштабирование
# ============================================================

def create_scale(max_value: int) -> float:
    """
    Возвращает верхнюю границу шкалы.

    Для маленьких значений оставляем небольшой запас сверху,
    чтобы линия не упиралась непосредственно в верхнюю границу.
    """

    if max_value <= 0:
        return 1.0

    return max(
        float(max_value),
        1.0,
    )


def create_y_function(max_value: int):
    """
    Создаёт функцию преобразования значения в координату Y.

    В SVG координата Y увеличивается сверху вниз, поэтому
    большие значения должны находиться выше.
    """

    scale = create_scale(max_value)

    def y(value: int) -> float:
        return (
            PADDING_TOP
            + CHART_HEIGHT
            - (value / scale) * CHART_HEIGHT
        )

    return y


# ============================================================
# Генерация polyline
# ============================================================

def create_polyline(
    points: list[Point],
    y_function,
) -> str:
    """
    Преобразует набор точек в SVG polyline.
    """

    if not points:
        return ""

    if len(points) == 1:
        x_positions = [PADDING_LEFT + CHART_WIDTH / 2]
    else:
        x_step = CHART_WIDTH / (len(points) - 1)

        x_positions = [
            PADDING_LEFT + index * x_step
            for index in range(len(points))
        ]

    coordinates = []

    for x_position, point in zip(x_positions, points):
        coordinates.append(
            f"{x_position:.1f},{y_function(point.value):.1f}"
        )

    return " ".join(coordinates)


# ============================================================
# Генерация графика Views
# ============================================================

def create_views_chart(
    points: list[Point],
    output: Path,
) -> None:
    """
    Создаёт график просмотров.

    Для views используется одна линия.
    """

    if not points:
        return

    max_value = max(point.value for point in points)

    y = create_y_function(max_value)

    line = create_polyline(
        points,
        y,
    )

    latest = points[-1]

    latest_y = y(latest.value)

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
      font-size: 11px;
      font-weight: 600;
      fill: {COLOR_TEXT};
    }}

    .label {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 9px;
      fill: {COLOR_MUTED};
    }}

    .value {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 9px;
      font-weight: 600;
      fill: {COLOR_DAILY};
    }}
  </style>

  <text
    x="{PADDING_LEFT}"
    y="13"
    class="title"
  >
    GitHub views
  </text>

  <line
    x1="{PADDING_LEFT}"
    y1="{PADDING_TOP + CHART_HEIGHT}"
    x2="{PADDING_LEFT + CHART_WIDTH}"
    y2="{PADDING_TOP + CHART_HEIGHT}"
    stroke="{COLOR_GRID}"
    stroke-width="1"
  />

  <polyline
    points="{line}"
    fill="none"
    stroke="{COLOR_DAILY}"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
  />

  <circle
    cx="{PADDING_LEFT + CHART_WIDTH}"
    cy="{latest_y:.1f}"
    r="2.5"
    fill="{COLOR_DAILY}"
  />

  <!--
    Значение находится СПРАВА от конечной точки.

    Это возможно благодаря увеличенному PADDING_RIGHT.
    Поэтому текст больше не пересекается с линией.
  -->
  <text
    x="{PADDING_LEFT + CHART_WIDTH + 6}"
    y="{latest_y + 3:.1f}"
    class="value"
  >
    {format_number(latest.value)}
  </text>

  <text
    x="{PADDING_LEFT}"
    y="{HEIGHT - 7}"
    class="label"
  >
    {escape(points[0].date)}
  </text>

  <text
    x="{WIDTH - PADDING_RIGHT}"
    y="{HEIGHT - 7}"
    text-anchor="end"
    class="label"
  >
    {escape(latest.date)}
  </text>

</svg>
"""

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        svg,
        encoding="utf-8",
    )


# ============================================================
# Генерация графика Clones
# ============================================================

def create_clones_chart(
    points: list[Point],
    output: Path,
) -> None:
    """
    Создаёт график клонирований.

    На графике две линии:

    1. Daily
       Количество клонирований за конкретный день.

    2. Total
       Накопительное количество клонирований.

    Важный момент:
    обе линии используют РАЗНЫЕ шкалы.

    Это необходимо потому, что cumulative-значение постепенно
    становится значительно больше дневного. Если использовать
    одну шкалу, Daily-линия практически прижмётся к нулю.
    """

    if not points:
        return

    # --------------------------------------------------------
    # Daily
    # --------------------------------------------------------

    daily_values = [
        point.value
        for point in points
    ]

    daily_max = max(daily_values)

    daily_y = create_y_function(
        daily_max,
    )

    # --------------------------------------------------------
    # Cumulative
    # --------------------------------------------------------

    cumulative_points: list[Point] = []

    total = 0

    for point in points:
        total += point.value

        cumulative_points.append(
            Point(
                date=point.date,
                value=total,
            )
        )

    cumulative_max = cumulative_points[-1].value

    cumulative_y = create_y_function(
        cumulative_max,
    )

    # --------------------------------------------------------
    # X coordinates
    # --------------------------------------------------------

    if len(points) == 1:
        x_positions = [
            PADDING_LEFT + CHART_WIDTH / 2
        ]
    else:
        x_step = CHART_WIDTH / (len(points) - 1)

        x_positions = [
            PADDING_LEFT + index * x_step
            for index in range(len(points))
        ]

    # --------------------------------------------------------
    # Daily line
    # --------------------------------------------------------

    daily_coordinates = []

    for x_position, point in zip(
        x_positions,
        points,
    ):
        daily_coordinates.append(
            f"{x_position:.1f},{daily_y(point.value):.1f}"
        )

    daily_line = " ".join(
        daily_coordinates
    )

    # --------------------------------------------------------
    # Cumulative line
    # --------------------------------------------------------

    cumulative_coordinates = []

    for x_position, point in zip(
        x_positions,
        cumulative_points,
    ):
        cumulative_coordinates.append(
            f"{x_position:.1f},{cumulative_y(point.value):.1f}"
        )

    cumulative_line = " ".join(
        cumulative_coordinates
    )

    # --------------------------------------------------------
    # Последние точки
    # --------------------------------------------------------

    latest_daily = points[-1]
    latest_total = cumulative_points[-1]

    latest_x = x_positions[-1]

    latest_daily_y = daily_y(
        latest_daily.value
    )

    latest_total_y = cumulative_y(
        latest_total.value
    )

    # --------------------------------------------------------
    # Разведение подписей
    #
    # Значения подписываются справа от точек.
    #
    # Но если точки находятся близко по вертикали, текст может
    # столкнуться. Поэтому дополнительно проверяем расстояние.
    # --------------------------------------------------------

    daily_label_y = latest_daily_y + 3
    total_label_y = latest_total_y + 3

    minimum_label_distance = 12

    if abs(daily_label_y - total_label_y) < minimum_label_distance:
        if daily_label_y <= total_label_y:
            daily_label_y -= minimum_label_distance / 2
            total_label_y += minimum_label_distance / 2
        else:
            total_label_y -= minimum_label_distance / 2
            daily_label_y += minimum_label_distance / 2

    # Не позволяем тексту выйти за вертикальные границы SVG.
    daily_label_y = max(
        10,
        min(HEIGHT - 18, daily_label_y),
    )

    total_label_y = max(
        10,
        min(HEIGHT - 18, total_label_y),
    )

    # --------------------------------------------------------
    # SVG
    # --------------------------------------------------------

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
      fill: {COLOR_TEXT};
    }}

    .label {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 9px;
      fill: {COLOR_MUTED};
    }}

    .legend {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 8px;
      fill: {COLOR_TEXT};
    }}

    .daily-value {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 9px;
      font-weight: 600;
      fill: {COLOR_DAILY};
    }}

    .total-value {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      font-size: 9px;
      font-weight: 600;
      fill: {COLOR_TOTAL};
    }}
  </style>

  <!-- ======================================================
       Заголовок
       ====================================================== -->

  <text
    x="{PADDING_LEFT}"
    y="13"
    class="title"
  >
    GitHub clones
  </text>


  <!-- ======================================================
       Легенда
       ====================================================== -->

  <line
    x1="{PADDING_LEFT + 82}"
    y1="9"
    x2="{PADDING_LEFT + 91}"
    y2="9"
    stroke="{COLOR_DAILY}"
    stroke-width="2"
    stroke-linecap="round"
  />

  <text
    x="{PADDING_LEFT + 95}"
    y="12"
    class="legend"
  >
    Daily
  </text>

  <line
    x1="{PADDING_LEFT + 128}"
    y1="9"
    x2="{PADDING_LEFT + 137}"
    y2="9"
    stroke="{COLOR_TOTAL}"
    stroke-width="2"
    stroke-linecap="round"
  />

  <text
    x="{PADDING_LEFT + 141}"
    y="12"
    class="legend"
  >
    Total
  </text>


  <!-- ======================================================
       Нижняя базовая линия
       ====================================================== -->

  <line
    x1="{PADDING_LEFT}"
    y1="{PADDING_TOP + CHART_HEIGHT}"
    x2="{PADDING_LEFT + CHART_WIDTH}"
    y2="{PADDING_TOP + CHART_HEIGHT}"
    stroke="{COLOR_GRID}"
    stroke-width="1"
  />


  <!-- ======================================================
       Daily
       ====================================================== -->

  <polyline
    points="{daily_line}"
    fill="none"
    stroke="{COLOR_DAILY}"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
  />

  <circle
    cx="{latest_x:.1f}"
    cy="{latest_daily_y:.1f}"
    r="2.5"
    fill="{COLOR_DAILY}"
  />


  <!-- ======================================================
       Total
       ====================================================== -->

  <polyline
    points="{cumulative_line}"
    fill="none"
    stroke="{COLOR_TOTAL}"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
  />

  <circle
    cx="{latest_x:.1f}"
    cy="{latest_total_y:.1f}"
    r="2.5"
    fill="{COLOR_TOTAL}"
  />


  <!-- ======================================================
       Конечные значения
       
       ВАЖНО:
       подписи находятся СПРАВА от точек, а не слева.
       
       latest_x + 6 гарантирует зазор между точкой и текстом.
       Дополнительный PADDING_RIGHT гарантирует, что текст
       остаётся внутри SVG.
       ====================================================== -->

  <text
    x="{latest_x + 6:.1f}"
    y="{daily_label_y:.1f}"
    class="daily-value"
  >
    {format_number(latest_daily.value)}
  </text>

  <text
    x="{latest_x + 6:.1f}"
    y="{total_label_y:.1f}"
    class="total-value"
  >
    {format_number(latest_total.value)}
  </text>


  <!-- ======================================================
       Даты
       ====================================================== -->

  <text
    x="{PADDING_LEFT}"
    y="{HEIGHT - 7}"
    class="label"
  >
    {escape(points[0].date)}
  </text>

  <text
    x="{WIDTH - PADDING_RIGHT}"
    y="{HEIGHT - 7}"
    text-anchor="end"
    class="label"
  >
    {escape(latest_daily.date)}
  </text>

</svg>
"""

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        svg,
        encoding="utf-8",
    )


# ============================================================
# Main
# ============================================================

def main() -> None:
    """
    Точка входа генератора.

    Генерируем два графика:

        traffic/charts/views.svg
        traffic/charts/clones.svg
    """

    CHARTS.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Views
    # --------------------------------------------------------

    views = load_snapshots(
        "views"
    )

    create_views_chart(
        views,
        CHARTS / "views.svg",
    )

    # --------------------------------------------------------
    # Clones
    # --------------------------------------------------------

    clones = load_snapshots(
        "clones"
    )

    create_clones_chart(
        clones,
        CHARTS / "clones.svg",
    )


# ============================================================
# Script entry point
# ============================================================

if __name__ == "__main__":
    main()
