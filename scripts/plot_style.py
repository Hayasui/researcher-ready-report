# -*- coding: utf-8 -*-
"""研究备忘录配图的通用样式与画法。

只用 matplotlib，不依赖 pandas。用法：

    import plot_style as ps
    ps.setup()                       # 注册中文字体 + 设定配色与字体大小
    fig, ax = ps.figure()
    ps.hbar(ax, labels, counts, base)   # counts 是计数，base 是基数，误差棒自动算
    ps.save(fig, "figures/fig01_xxx.png", "图 1　结论式标题")

约定：凡是比例都画 ME 误差棒，凡是图都写出 n。分母逐题不同是这类数据的常态，
不写 n 的图没法被正文引用。
"""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

Z = 1.959964          # 95% 区间

# 系统里能找到的中文字体，按优先级排；Windows 用雅黑，macOS 用苹方，Linux 用思源
CJK_CANDIDATES = (
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/YuGothM.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
)

INK = "#2B2F36"
BLUE = "#3C6E9F"
TEAL = "#4E8F86"
ORANGE = "#C97B3C"
GREY = "#A9B0BA"


def pct(c, n):
    return 100.0 * c / n if n else float("nan")


def moe(c, n):
    """比例的 ME，单位百分点。"""
    if not n:
        return float("nan")
    p = float(c) / n
    return Z * math.sqrt(max(p * (1 - p), 1e-12) / n) * 100.0


def setup(font_candidates=CJK_CANDIDATES):
    """注册中文字体并设定全局样式。找不到中文字体时退回默认字体，图里的中文会变方块，
    所以画完要看一眼。"""
    family = "DejaVu Sans"
    for path in font_candidates:
        if os.path.exists(path):
            font_manager.fontManager.addfont(path)
            family = font_manager.FontProperties(fname=path).get_name()
            break
    plt.rcParams["font.sans-serif"] = [family, "DejaVu Sans"]
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["axes.facecolor"] = "white"
    plt.rcParams["axes.edgecolor"] = "#B8BEC7"
    plt.rcParams["axes.labelcolor"] = INK
    plt.rcParams["text.color"] = INK
    plt.rcParams["xtick.color"] = "#5A6270"
    plt.rcParams["ytick.color"] = INK
    plt.rcParams["axes.titlesize"] = 12
    plt.rcParams["axes.titleweight"] = "bold"
    return family


def figure(w=7.4, h=4.0, ncols=1, width_ratios=None):
    """开一张图。ncols>1 时返回 (fig, axes 列表)。"""
    if ncols == 1:
        fig, ax = plt.subplots(figsize=(w, h))
        return fig, [ax]
    kw = {"width_ratios": width_ratios} if width_ratios else {}
    fig, axes = plt.subplots(1, ncols, figsize=(w, h), gridspec_kw=kw)
    return fig, list(axes)


def strip(ax, keep=("bottom",)):
    """去掉多余的边框与网格外的装饰。"""
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(s in keep)


def hbar(ax, labels, counts, base, colors=None, xmax=None, sort=True, label_fmt="%.1f"):
    """水平条 + ME 误差棒。labels 与 counts 等长；base 是基数，用来算 ME 与写 n。
    同一条可选多组基数（分组场景请改用 grouped_hbar）。"""
    errs = [moe(c, base) for c in counts]
    vals = [pct(c, base) for c in counts]
    if sort:
        order = sorted(range(len(vals)), key=lambda i: -vals[i])
    else:
        order = list(range(len(vals)))
    y = list(range(len(order)))[::-1]
    if colors is None:
        colors = [BLUE] * len(order)
    elif isinstance(colors, str):
        colors = [colors] * len(order)
    ax.barh(y, [vals[i] for i in order], xerr=[errs[i] for i in order],
            color=[colors[i] if len(colors) == len(order) else colors[order[k]]
                   for k, i in enumerate(order)],
            height=0.62,
            error_kw=dict(ecolor="#6C7480", elinewidth=0.9, capsize=2.4))
    ax.set_yticks(y)
    ax.set_yticklabels([labels[i] for i in order])
    top = max(v + e for v, e in zip(vals, errs))
    ax.set_xlim(0, xmax or top * 1.28)
    for yy, i in zip(y, order):
        ax.text(vals[i] + errs[i] + ax.get_xlim()[1] * 0.012, yy, label_fmt % vals[i],
                va="center", fontsize=8.5, color=INK)
    ax.set_xlabel("占比（%%，误差棒为 ME）　n = %d" % base, fontsize=9)
    ax.grid(axis="x", color="#E4E8EC", linewidth=0.8)
    ax.set_axisbelow(True)
    strip(ax, keep=("bottom",))
    return ax


def grouped_hbar(ax, labels, series, xlim=None):
    """分组水平条。series 是 [(名字, counts, base), ...]，各组的基数可以不同，
    但调用方要在图注里写清「分母是否相同」。"""
    n = len(series)
    y = list(range(len(labels)))[::-1]
    hh = 0.8 / n
    for k, (name, counts, base) in enumerate(series):
        off = (k - (n - 1) / 2.0) * hh
        vals = [pct(c, base) for c in counts]
        errs = [moe(c, base) for c in counts]
        ax.barh([yy + off for yy in y], vals, xerr=errs, height=hh,
                color=[BLUE, TEAL, ORANGE, GREY][k % 4],
                label="%s（n=%d）" % (name, base),
                error_kw=dict(ecolor="#6C7480", elinewidth=0.9, capsize=2.2))
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    top = ax.get_xlim()[1]
    ax.set_xlim(0, xlim or top)
    ax.set_xlabel("占比（%，误差棒为 ME）", fontsize=9)
    ax.grid(axis="x", color="#E4E8EC", linewidth=0.8)
    ax.set_axisbelow(True)
    strip(ax, keep=("bottom",))
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    return ax


def stacked_pct_hbar(ax, labels, parts, colors=(TEAL, "#E4E8EC")):
    """百分比堆叠条。parts[0] 是要突出的那一部分是计数，parts 里其余项已经算好补足。
    parts 形如 [(名字, counts, base), (名字, 补足 counts, base)]，第二项一般用
    base - count 传进来即可。标签写在条内与条外各一处。"""
    name0, c0, base0 = parts[0]
    y = list(range(len(labels)))[::-1]
    v0 = [pct(c, b) for c, b in zip(c0, base0)]
    ax.barh(y, v0, color=colors[0], height=0.58)
    ax.barh(y, [100 - v for v in v0], left=v0, color=colors[1], height=0.58)
    ax.set_yticks(y)
    ax.set_yticklabels(["%s\n（n=%d）" % (lab, b) for lab, b in zip(labels, base0)])
    ax.set_xlim(0, 100)
    for yy, v, c, b in zip(y, v0, c0, base0):
        if v >= 14:
            ax.text(v - 1.5, yy, "%.1f%%" % v, va="center", ha="right", fontsize=9,
                    color="white", fontweight="bold")
        else:
            ax.text(v + 1.5, yy, "%.1f%%" % v, va="center", ha="left", fontsize=9,
                    color=INK, fontweight="bold")
        ax.text(101, yy, "%d / %d" % (c, b), va="center", fontsize=8.5, color="#5A6270")
    ax.set_xlabel("占比（%%，深色为「%s」）" % name0, fontsize=9)
    ax.grid(axis="x", color="#EEF1F4", linewidth=0.8)
    ax.set_axisbelow(True)
    strip(ax, keep=("bottom",))
    return ax


def line_with_notes(ax, xs, counts, bases, color=ORANGE, ylim=(0, 105), ylabel=None):
    """折线 + 每个点旁边写「比例 ／ n」。适合「按档位看某个比例怎么变」这一型。"""
    vals = [pct(c, b) for c, b in zip(counts, bases)]
    ax.plot(range(len(xs)), vals, marker="o", color=color, linewidth=2, markersize=6)
    for i, (v, b) in enumerate(zip(vals, bases)):
        ax.text(i, v + 4, "%.0f%%\nn=%d" % (v, b), ha="center", fontsize=8,
                color="#5A6270")
    ax.set_xticks(range(len(xs)))
    ax.set_xticklabels(xs, rotation=28, ha="right", fontsize=8.5)
    ax.set_ylim(*ylim)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(axis="y", color="#E4E8EC", linewidth=0.8)
    ax.set_axisbelow(True)
    strip(ax, keep=("bottom",))
    return ax


def save(fig, path, title=None, y=1.02):
    """写盘。title 给整张图的结论式标题，多面板时写在图上沿。"""
    if title:
        fig.suptitle(title, fontsize=13, fontweight="bold", y=y)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path
