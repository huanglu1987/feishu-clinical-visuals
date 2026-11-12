"""Copy into the task workspace and replace the fictional data before use.

Requires matplotlib. Run: python3 comparison-template.py --output-prefix work/demo
This is an editable design template, not an estimator or a generic data importer.
"""

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D


@dataclass(frozen=True)
class Row:
    group: str
    label: str
    value: float
    control: float | None
    source: str


# A control must come from the same study as its paired value; None is not zero.
ROWS = [
    Row("研究终点 A", "研究 A｜试验方案 A\n第 24 周 · 同研究内对照", 46.0, 12.0, "虚构数据 [D1]"),
    Row("研究终点 A", "研究 B｜试验方案 B\n第 24 周 · 同研究内对照", 33.0, 8.0, "虚构数据 [D2]"),
    Row("探索性终点 B（单列，不与上组比较）", "研究 C｜探索性队列\n第 12 周 · 对照数据未报告", 24.0, None, "虚构数据 [D3]"),
]
TITLE = "研究结果的描述性展示｜虚构示例"
X_LABEL = "对应终点的应答比例（%）"
NOTES = [
    "图内数字均为虚构，仅演示版式；不得用于医学判断。来源：示例数据 [D1–D3]。",
    "连接线仅连接同一研究内的两组，不表示置信区间；缺失对照不按零处理。",
    "不同研究的口径和人群须分别核实，本图不用于跨研究疗效排名。",
]
BLUE, GRAY, INK = "#2878D8", "#A7A6A0", "#20252B"


def validate_rows(rows):
    if not rows:
        raise ValueError("No rows to plot")
    for row in rows:
        if not row.label.strip() or not row.group.strip() or not row.source.strip():
            raise ValueError("Each row needs a group, label and source")
        for value in (row.value, row.control):
            if value is not None and (not math.isfinite(value) or not 0 <= value <= 100):
                raise ValueError("This percentage template expects finite values from 0 to 100")
        if row.value is None:
            raise ValueError("Missing primary value: annotate it separately instead of plotting zero")


def find_cjk_font():
    for name in ("Noto Sans CJK SC", "Noto Sans SC", "Arial Unicode MS", "Microsoft YaHei", "PingFang SC"):
        try:
            font_manager.findfont(name, fallback_to_default=False)
            return name
        except ValueError:
            continue
    raise RuntimeError("No supported Chinese font found; configure a local CJK font before rendering")


def draw(prefix):
    validate_rows(ROWS)
    outputs = [prefix.with_suffix(ext) for ext in (".png", ".svg")]
    if any(path.exists() for path in outputs):
        raise FileExistsError("Output exists; choose a new prefix to preserve previous work")
    prefix.parent.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": find_cjk_font(), "font.size": 12,
                         "axes.unicode_minus": False, "svg.fonttype": "none"})
    positions, headers, cursor, previous = [], [], 0.0, None
    for row in ROWS:
        if row.group != previous:
            headers.append((cursor, row.group))
            cursor += 0.85
            previous = row.group
        positions.append(cursor)
        cursor += 1.2
    fig, ax = plt.subplots(figsize=(10.8, max(5.6, cursor * 0.6 + 2.0)))
    fig.subplots_adjust(left=0.43, right=0.94, top=0.79, bottom=0.24)
    fig.text(0.035, 0.945, TITLE, fontsize=19, weight="bold", color=INK)
    fig.legend(handles=[Line2D([], [], color=BLUE, marker="o", linestyle="", label="试验组"),
                        Line2D([], [], color=GRAY, marker="s", linestyle="", label="同研究对照组")],
               loc="upper left", bbox_to_anchor=(0.027, 0.91), ncol=2, frameon=False)
    ax.set_xlim(0, 100)
    ax.set_ylim(cursor - 0.45, -0.45)
    ax.set_xticks(range(0, 101, 20))
    ax.set_yticks(positions, [row.label for row in ROWS])
    ax.tick_params(axis="both", length=0, pad=9, labelcolor=INK)
    ax.grid(axis="x", color="#E3E2DD", linewidth=0.8)
    ax.set_axisbelow(True)
    for y, text in headers:
        ax.text(-0.77, y, text, transform=ax.get_yaxis_transform(), fontsize=12,
                weight="bold", color=BLUE, va="center", clip_on=False)
    for row, y in zip(ROWS, positions):
        if row.control is not None:
            ax.plot([row.control, row.value], [y, y], color="#E3E2DD", lw=2.5, zorder=2)
            ax.scatter(row.control, y, color=GRAY, marker="s", s=55, zorder=3)
            ax.annotate(f"{row.control:g}%", (row.control, y), xytext=(0, 12),
                        textcoords="offset points", ha="center", color="#5E6570", fontsize=10)
        ax.scatter(row.value, y, color=BLUE, s=80, edgecolor="white", linewidth=1, zorder=4)
        offset = 9 if row.value <= 90 else -9
        ax.annotate(f"{row.value:g}%", (row.value, y), xytext=(offset, -12),
                    textcoords="offset points", ha="left" if offset > 0 else "right", color=INK)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#C5C6C8")
    ax.set_xlabel(X_LABEL, labelpad=12, color="#5E6570")
    for i, note in enumerate(NOTES):
        fig.text(0.035, 0.115 - i * 0.032, note, fontsize=10, color="#5E6570")
    for path in outputs:
        fig.savefig(path, dpi=180, facecolor="white")
    plt.close(fig)
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args()
    for output in draw(args.output_prefix):
        print(output)
