"""Penyusunan data Edisi 011: harga pasca-Lebaran, turun atau lengket.

Tanpa panggilan jaringan. Edisi ini memakai ulang panen PIHPS yang dilakukan
pada Edisi 008 (berkas mentah JSON per Rabu per komoditas di
`edisi/008/data/mentah/pihps/` dan tabel rapi `edisi/008/data/harga-nasional-mingguan.csv`,
beserta `edisi/008/data/tanggal-ramadan.csv`, kalender 1440-1447 H yang
terverifikasi dari ketetapan resmi). Alasannya: jendela mingguan Edisi 008
sudah mencakup 42 hari pasca-Lebaran, lebih panjang dari kebutuhan pengukuran
+H30 dan +H42 di edisi ini.

Definisi metrik (diulang eksplisit agar edisi ini berdiri sendiri):
- basis(k, H)      : rerata harga nasional komoditas k pada minggu-minggu
                     70 s.d. 35 hari sebelum 1 Ramadan musim H (aturan identik
                     dengan Edisi 008).
- kenaikan puncak  : maksimum harga/basis pada jendela H-35 s.d. H+8 relatif
                     Lebaran (kurang 1). Musim dengan kenaikan < 2% tidak diuji
                     (tiada kenaikan yang bisa diamati kelengketannya).
- sisa (+H30/+H42) : harga/basis pada snapshot Rabu terdekat (toleransi 4 hari).
- indeks lengket   : (sisa - 1) / kenaikan puncak. =0 berarti pulih penuh ke
                     basis (atau jeblok di bawahnya bila negatif); =1 berarti
                     kenaikan bertahan penuh; >1 berarti harga malah naik
                     setelah Lebaran (rezim berbeda, bukan kelengketan musiman).

Output: data/harga-lengket.csv (pasangan komoditas x musim) dan salinan
data/tanggal-ramadan.csv.

Jalankan: python3 unduh_data.py
"""
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

FOLDER = Path(__file__).parent
SUMBER = FOLDER.parent / "008" / "data"
TOLERANS_SNAP_HARI = 4
AMBANG_NAIK = 0.02


def main() -> None:
    assert (SUMBER / "harga-nasional-mingguan.csv").exists(), (
        "Panen Edisi 008 tidak ditemukan di workspace; pulihkan dari bundel "
        "(tag edisi-008) bila perlu.")
    df = pd.read_csv(SUMBER / "harga-nasional-mingguan.csv", parse_dates=["tanggal"])
    tgl = pd.read_csv(SUMBER / "tanggal-ramadan.csv",
                      parse_dates=["puasa_mulai", "lebaran"]).set_index("tahun_hijri")

    baris = []
    for kom, g in df.groupby("komoditas"):
        g = g.set_index("tanggal").sort_index()
        for H, r in tgl.iterrows():
            erwel = (g.index - r.lebaran).days
            hr_p = (g.index - r.puasa_mulai).days
            basis = g[(hr_p >= -70) & (hr_p <= -35)]["harga_nasional"].mean()
            if not np.isfinite(basis):
                continue
            rmusim = g[(erwel >= -35) & (erwel <= 8)]
            if len(rmusim) < 6:
                continue
            rel_puncak = float((rmusim["harga_nasional"] / basis).max())
            naik = rel_puncak - 1.0
            diuji = naik >= AMBANG_NAIK

            def snap(target):
                j = np.abs(erwel.values - target)
                if j.min() > TOLERANS_SNAP_HARI:
                    return np.nan
                return float(g["harga_nasional"].values[np.argmin(j)] / basis)

            s30, s42 = snap(30), snap(42)
            baris.append({
                "komoditas": kom, "tahun_hijri": int(H), "basis": round(basis, 2),
                "rel_puncak": round(rel_puncak, 4), "naik_pct": round(naik * 100, 2),
                "rel_sisa30": np.nan if np.isnan(s30) else round(s30, 4),
                "rel_sisa42": np.nan if np.isnan(s42) else round(s42, 4),
                "diuji": bool(diuji),
                "lengket30": np.nan if (not diuji or np.isnan(s30)) else round((s30 - 1) / naik, 3),
                "lengket42": np.nan if (not diuji or np.isnan(s42)) else round((s42 - 1) / naik, 3),
            })

    out = pd.DataFrame(baris).sort_values(["komoditas", "tahun_hijri"])
    out.to_csv(FOLDER / "data" / "harga-lengket.csv", index=False)
    (FOLDER / "data").mkdir(exist_ok=True)
    shutil.copy(SUMBER / "tanggal-ramadan.csv", FOLDER / "data" / "tanggal-ramadan.csv")
    uji = out[out.diuji]
    print("pasangan komoditas-musim:", len(out), "| yang diuji (naik >= 2%):", len(uji))
    print("median lengket +H30 per komoditas:")
    print(uji.groupby("komoditas")["lengket30"].median().sort_values(ascending=False).round(2).to_string())


if __name__ == "__main__":
    main()
