"""Unduh Statistik PLN dan ekstrak tabel runtun waktu ke CSV.

- Sumber: https://www.pln.co.id/webapi/media/file/webkorp/asset/Statistik{tahun}.pdf
- Tabel yang diambil (bagian "Data Runtun Waktu"):
  Energi Terjual per Kelompok Pelanggan (GWh)         -> pln-terjual_gwh.csv
  Energi Terjual Rata-rata per Kelompok (kWh)         -> pln-rerata_kwh.csv
  Jumlah Pelanggan per Kelompok Pelanggan             -> pln-pelanggan.csv
- Dua edisi buku (2023 & 2024) diparse; bila satu tahun muncul di dua buku dan
  selisihnya kecil, diambil rata-rata. Jika selisihnya besar (mis. lay out salah
  ketik resmi: pju_2015 = 156.782 di buku 2023 vs 186.118 di buku 2024 dengan
  kolom total yang cocok masing-masing), edisi TERBARU yang dipakai.
- Kolom total/"lainnya" dibuang; konversi format ID ("1.012.089,00" -> 1012089.00).

Jalankan: python3 unduh_data.py   (butuh internet, paket pdfplumber)
"""
import json
import re
import urllib.request
from itertools import chain
from pathlib import Path

import pdfplumber

DIR = Path(__file__).resolve().parent
MENTAH = DIR / "data" / "mentah" / "pln"
URL = "https://www.pln.co.id/webapi/media/file/webkorp/asset/Statistik{tahun}.pdf"

KELOMPOK = ["rumah_tangga", "industri", "bisnis", "sosial", "gdg_pemerintah", "pju"]
JUDUL = {
    "terjual_gwh": re.compile(r"Tabel\s*/?\w*\s*\d+\s*[:：]?\s*Energi\s+Terjual\s+per\s+Kelompok\s+Pelanggan\s*\(GWh\)", re.I),
    "rerata_kwh": re.compile(r"Tabel\s*/?\w*\s*\d+\s*[:：]?\s*Energi\s+Terjual\s+Rata-rata\s+per\s+Kelompok\s+Pelanggan\s*\(kWh\)[^\n]*", re.I),
    "pelanggan": re.compile(r"Tabel\s*/?\w*\s*\d+\s*[:：]?\s*Jumlah\s+Pelanggan\s+per\s+Kelompok\s+Pelanggan[^\n]*", re.I),
}
BARIS_TAHUN = re.compile(r"^(20\d\d)\s+((?:[\(\)\d\.,\-]+\s+){6,10}[\(\)\d\.,\-]+)$", re.M)
JUDUL_BERIKUT = re.compile(r"Tabel\s*/?\w*\s*\d+\s*[:：]")


def angka(s: str) -> float:
    """'1.012.089,00' -> 1012089.00 ; '-' -> 0 ; '(0,79)' -> 0.79 (kolom delta diabaikan isinya)."""
    s = s.strip()
    if s == "-":
        return 0.0
    return float(s.strip("()").replace(".", "").replace(",", "."))


def unduh(tahun: int) -> Path:
    out = MENTAH / f"statistik-{tahun}.pdf"
    if out.exists() and out.stat().st_size > 100_000:
        return out
    req = urllib.request.Request(URL.format(tahun=tahun), headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=120).read()
    out.write_bytes(data)
    return out


def serut(teks: dict, pola: re.Pattern) -> dict:
    """Parse baris tahun di segmen teks antara judul tabel target dan judul tabel berikutnya."""
    out = {}
    for i in sorted(teks):
        t = teks[i]
        for m in pola.finditer(t):
            sisa = t[m.end():]
            potong = JUDUL_BERIKUT.search(sisa)
            if potong:
                sisa = sisa[: potong.start()]
            for r in BARIS_TAHUN.finditer(sisa):
                try:
                    vals = [angka(x) for x in r.group(2).split()]
                except ValueError:
                    continue
                if len(vals) >= 6:
                    out[int(r.group(1))] = vals[:6]
    return out


def main() -> None:
    MENTAH.mkdir(parents=True, exist_ok=True)
    buku = [2023, 2024]  # 2019-2022 tidak dibutuhkan untuk runtun; 2025 belum terbit per saat unduh
    kumpul = {}
    for th in buku:
        path = unduh(th)
        with pdfplumber.open(path) as pdf:
            teks = {i: (h.extract_text() or "") for i, h in enumerate(pdf.pages)}
        for kunci, pola in JUDUL.items():
            tabel = serut(teks, pola)
            for thn, vals in tabel.items():
                kumpul.setdefault(thn, {}).setdefault(kunci, {})[f"edisi_{th}"] = vals
            print(th, kunci, len(tabel), "tahun ter-parse")

    # pivot: rata-rata antar buku bila cocok; bila berbeda besar, pakai edisi baru
    TOLERANSI = 1.0  # satuan tabel (GWh / kWh / pelanggan)
    seri = {}
    for kunci in JUDUL:
        baris = {}
        for thn in sorted(kumpul):
            edisi = kumpul[thn].get(kunci, {})
            if not edisi:
                continue
            akum = None
            n = 0
            for v in list(edisi.values()):
                if len(v) < 6:
                    continue
                akum = list(v[:6]) if akum is None else [a + x for a, x in zip(akum, v[:6])]
                n += 1
            if not n:
                continue
            mean = [x / n for x in akum]
            if n > 1:
                baru = sorted(edisi)[-1]
                vbaru = edisi[baru][:6]
                beda = max(abs(m - b) for m, b in zip(mean, vbaru))
                if beda > TOLERANSI:
                    print(f"  konflik {kunci} {thn}: rata vs edisi {baru} beda {beda:.1f} -> pakai edisi {baru}")
                    mean = [float(x) for x in vbaru]
            baris[thn] = mean
        seri[kunci] = baris
        with open(DIR / "data" / f"pln-{kunci}.csv", "w") as f:
            f.write("tahun," + ",".join(KELOMPOK) + "\n")
            for thn, vals in baris.items():
                f.write(str(thn) + "," + ",".join(f"{v:.2f}" for v in vals) + "\n")

    (DIR / "data" / "mentah" / "pln-ekstrak.json").write_text(json.dumps(kumpul, indent=1))
    print("selesai: data/pln-*.csv tertulis")


if __name__ == "__main__":
    main()
