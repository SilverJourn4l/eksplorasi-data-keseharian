"""Pengambilan data Edisi 010: bentuk puncak mudik Lebaran.

Sumber tunggal yang bisa dibaca mesin: katalog HUBNET Kementerian Perhubungan,
"Data Harian Pergerakan Penumpang Angkutan Lebaran, Natal dan Tahun Baru"
(penerbit: Pusat Data dan Teknologi Informasi Kemenhub). Satu panggilan JSON
tanpa penyaring mengembalikan seluruh tabel: 325 baris = tiga event
(ANGLEB 2024, ANGLEB 2025, NATARU 2024 2025), lima moda, H-10 s.d. H+10/H+11.

- Mentah disimpan sekali di data/mentah/hubnet/data_event_kemenpar.json.
- Tabel rapi disalin ke data/pergerakan-event.csv (kolom:
  event, tanggal, periode, hari_relatif, moda, penumpang). hari_relatif:
  H 1 -> 0, H 2 -> 1, H + k -> 1+k, H - k -> -k.
- Katalog belum memuat ANGLEB 2026 (saat akses): itu dicatat di data/README.md
  dan kisaran 2026 dibaca dari rilis posko terpadu yang rutin.

Jalankan: python3 unduh_data.py
"""
import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

URL = ("https://hubnet.kemenhub.go.id/dataset/get-data-api/microstrategy/"
       "data_event_kemenpar?format=json")
FOLDER = Path(__file__).parent
MENTAH = FOLDER / "data" / "mentah" / "hubnet"


def hari_relatif(periode: str) -> int:
    p = periode.strip()
    if p.startswith("H -"):
        return -int(p[3:])
    if p.startswith("H +"):
        return 1 + int(p[3:])
    if p.startswith("H "):
        return int(p[2:]) - 1
    raise ValueError(f"periode tak dikenal: {periode!r}")


def main() -> None:
    MENTAH.mkdir(parents=True, exist_ok=True)
    cache = MENTAH / "data_event_kemenpar.json"
    if not cache.exists():
        req = urllib.request.Request(URL, headers={"User-Agent": "JurnalDataKeseharian/1.0 (riset publik)"})
        cache.write_bytes(urllib.request.urlopen(req, timeout=60).read())
        time.sleep(2)
    df = pd.DataFrame(json.loads(cache.read_text()))
    df["hari_relatif"] = df["periode"].map(hari_relatif)
    df = df[["event", "tanggal", "periode", "hari_relatif", "moda", "penumpang"]]
    df = df.sort_values(["event", "moda", "hari_relatif"]).reset_index(drop=True)
    df.to_csv(FOLDER / "data" / "pergerakan-event.csv", index=False)
    print("tersimpan:", len(df), "baris |", df["event"].value_counts().to_dict())


if __name__ == "__main__":
    main()
