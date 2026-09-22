"""Modul gaya grafik Jurnal Eksplorasi Data Keseharian.

Setiap edisi memakai modul ini supaya palet, tipografi, dan kaki sumber tetap sama.
Jalankan notebook dari folder edisi; gambar masuk ke gambar/ dan linkedin/gambar/.
"""

from pathlib import Path

import matplotlib.pyplot as plt

INK, INK2, AKSEN = "#22314F", "#5A6B8C", "#B3541E"
KERTAS, GRID = "#FAF9F5", "#D7D3CB"

MODE = {
    "readme": dict(figsize=(7.2, 4.6), dpi=200, fs=1.0, out=Path("gambar")),
    "linkedin": dict(figsize=(5.4, 6.75), dpi=200, fs=1.5, out=Path("linkedin/gambar")),
}


def terapkan():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "figure.facecolor": KERTAS,
        "axes.facecolor": KERTAS,
        "axes.edgecolor": GRID,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
    })


def idn(x, d=2):
    return f"{x:,.{d}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def dasar(mode, judul, sub, sumber, n):
    """Bingkai grafik standar: judul-pertanyaan, subjudul-jawaban, kaki sumber di kiri bawah."""
    m = MODE[mode]
    fig, ax = plt.subplots(figsize=m["figsize"])
    fs = m["fs"]
    fig.suptitle(judul, x=0.02, ha="left", fontsize=13 * fs, fontweight="bold", color=INK)
    ax.set_title(sub, loc="left", fontsize=10 * fs, color=INK2, pad=10)
    fig.text(0.02, -0.02, f"Sumber: {sumber} | n = {n}", fontsize=8 * fs, color=INK2)
    ax.grid(True, axis="x")
    ax.grid(False, axis="y")
    for sisi in ("top", "right"):
        ax.spines[sisi].set_visible(False)
    return fig, ax, fs


def simpan(fig, nama, mode):
    m = MODE[mode]
    m["out"].mkdir(parents=True, exist_ok=True)
    fig.savefig(m["out"] / f"{nama}.png", bbox_inches="tight", facecolor=KERTAS)
    plt.close(fig)


def kartu(mode, kop, judul, blok, kaki):
    """Kartu teks untuk karousel: kop edisi, judul besar, blok paragraf, kaki identitas.

    Pemanggil memecah baris panjang sendiri (matplotlib tidak membungkus teks otomatis).
    blok adalah daftar pasangan (warna, teks).
    """
    m = MODE[mode]
    fs = m["fs"]
    fig = plt.figure(figsize=m["figsize"])
    fig.text(0.08, 0.94, kop, fontsize=9 * fs, color=AKSEN, fontweight="bold")
    fig.text(0.08, 0.85, judul, fontsize=15 * fs, color=INK, fontweight="bold", va="top", linespacing=1.3)
    y = 0.66
    for warna, teks in blok:
        fig.text(0.08, y, teks, fontsize=10.5 * fs, color=warna, va="top", linespacing=1.55)
        y -= 0.055 * (teks.count("\n") + 1) + 0.045
    fig.text(0.08, 0.05, kaki, fontsize=8.5 * fs, color=INK2)
    return fig
