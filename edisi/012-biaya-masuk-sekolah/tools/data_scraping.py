"""Unduh & ekstrak data Edisi 012: biaya masuk sekolah.

Sumber: BPS, "Statistik Penunjang Pendidikan 2024" (Katalog 4301007, ~25 MB;
Susenas MSBP, data tahun ajaran 2023/2024; rilis 28 Mei 2025).
Unduh perlu internet sekali; URL unduh resmi pada halaman publikasi BPS
(token dapat kedaluwarsa, solusinya ambil ulang dari halaman publikasi
`bps.go.id` lalu timpa berkas PDF, alur cache membuatnya incremental).

Yang diparse:
- Tabel 2.1 (hal. 15 PDF berlabel; indeks-0 = 45): rata-rata total biaya
  pendidikan per murid setahun menurut karakteristik x jenjang (juta rupiah);
- Tabel 2.2 (indeks-0 = 46): proporsi 16 komponen biaya menurut jenjang (%).

Halaman mengandung watermark diagonal; fragmen huruf kadang menempel pada
angka ("d0,58", "p1,14", "0,2.6") sehingga dibersihkan terprogram. Karena
label komponen patah di sekitar baris angka, pemetaan label dilakukan lewat
urutan komponen yang diketahui (bukan pencocokan teks), lalu divalidasi:
jumlah tiap kolom harus 100 +/- 0,2 dan setiap sel cocok dengan angka pada
publikasi (verifikasi manual yang disalin di bawah).

Jalankan: python3 unduh_data.py
"""
import re
import urllib.request
from pathlib import Path

import pdfplumber

URL_DL = ("https://web-api.bps.go.id/download.php?f=HAYZThEY0snFKySabYUi02UySGw4TjkxYTRDRnJGZGs0U"
          "WFzMXAweUhDMy8rMkhhUG1nbmwrb0xOczhSdy9kcHJLMDNDR0lQbUFZZlJucVBvVGJrSStMWE92dE5CSmJ2WlZkN"
          "S9La1FZWFE5VjJ0T3A1bVFRRHp5TlBHS3VFVDl4UEMwZEdNMkJrR2tieUZ1bmQyeTUyekZBRm0wVFhWVnZBSFI2"
          "U255bmhjSEtDc1dDS0d5OXhqcTYvL1FVd244UXBkRHRNSEZ3WlNyNFdFcVZXUkZDdG1nTDRnVWxNUUNGQUtVbFV"
          "pS1l4WlNUUEYwMmR0cFdIUVdEVy9XNENTNDFwTUgxUHZycFdzZFNUdW8=")
FOLDER = Path(__file__).parent
PDF_PATH = FOLDER / "data" / "mentah" / "spp-2024.pdf"
HAL_TOTAL, HAL_KOMPONEN = 45, 46  # indeks-0: Tabel 2.1 dan Tabel 2.2

# Urutan 16 komponen Tabel 2.2, dengan nama kanonik untuk CSV
KOMPONEN_URUT = [
    "Uang Pendaftaran", "SPP/Uang Kuliah Tunggal (UKT)", "Komite Sekolah",
    "Ekstrakurikuler", "Baju Sekolah dan Perlengkapannya",
    "Buku Pelajaran/Panduan/Diktat", "Lembar Kerja Siswa (LKS)",
    "Alat Tulis dan Perlengkapan Lainnya", "Praktikum/Keterampilan dan Bahan Penunjangnya",
    "Kursus yang Diselenggarakan Sekolah", "Evaluasi/Ujian",
    "Kunjungan Edukatif (Study Tour)", "Pendukung Pembelajaran", "Lainnya",
    "Uang Saku", "Uang Transpor",
]
# Verifikasi manual dari halaman tabel (persen): dipakai sebagai aserti
KOMPONEN_ASERTI = {
    "Uang Pendaftaran": (2.13, 3.36, 3.97, 5.05),
    "SPP/Uang Kuliah Tunggal (UKT)": (4.88, 4.75, 7.69, 33.47),
    "Komite Sekolah": (1.13, 1.40, 1.91, 0.11),
    "Ekstrakurikuler": (0.35, 0.37, 0.23, 0.07),
    "Baju Sekolah dan Perlengkapannya": (7.62, 6.34, 4.91, 0.66),
    "Buku Pelajaran/Panduan/Diktat": (1.33, 0.96, 0.91, 1.30),
    "Lembar Kerja Siswa (LKS)": (1.80, 1.30, 0.94, 0.11),
    "Alat Tulis dan Perlengkapan Lainnya": (3.46, 2.42, 1.84, 0.76),
    "Praktikum/Keterampilan dan Bahan Penunjangnya": (0.19, 0.19, 0.58, 0.82),
    "Kursus yang Diselenggarakan Sekolah": (0.13, 0.06, 0.10, 0.03),
    "Evaluasi/Ujian": (0.14, 0.26, 0.30, 0.64),
    "Kunjungan Edukatif (Study Tour)": (0.38, 1.14, 1.12, 0.32),
    "Pendukung Pembelajaran": (0.50, 1.19, 1.64, 2.55),
    "Lainnya": (0.93, 1.31, 0.75, 0.74),
    "Uang Saku": (61.44, 55.88, 50.98, 35.13),
    "Uang Transpor": (13.60, 19.09, 22.11, 18.25),
}


def angka_id(s: str):
    """Parse angka format Indonesia (koma desimal) dari fragmen kotor."""
    s = re.sub(r"[^\d\.,]", "", s or "")
    if s.count(",") == 1 and s.count(".") > 0:  # titik liar watermark: "0,2.6" -> "0,26"
        s = s.replace(".", "")
    if re.fullmatch(r"\d+,\d{2}", s):
        return float(s.replace(",", "."))
    if re.fullmatch(r"\d+", s):
        return float(s)
    return None


def unduh() -> None:
    if PDF_PATH.exists() and PDF_PATH.stat().st_size > 20_000_000:
        print(f"cache: {PDF_PATH.name} ({PDF_PATH.stat().st_size:,} B)")
        return
    req = urllib.request.Request(URL_DL, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=300).read()
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    PDF_PATH.write_bytes(data)


def parse_total(pdf) -> None:
    import csv
    t1 = pdf.pages[HAL_TOTAL].extract_text() or ""
    baris1 = {
        "Total": "total", "20% Teratas": "kelompok_20_atas",
        "40% Menengah": "kelompok_40_tengah", "40% Terbawah": "kelompok_40_bawah",
        "Perkotaan": "perkotaan", "Perdesaan": "perdesaan",
    }
    n = 0
    with open(FOLDER / "data" / "spp-total-karakteristik.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kelompok", "sd", "smp", "sma_smk", "pt"])
        for line in t1.splitlines():
            for kunci, slug in baris1.items():
                if line.strip().startswith(kunci):
                    v = line.strip().split()
                    nums = [a for a in (angka_id(x) for x in v) if a is not None]
                    if len(nums) >= 4:
                        w.writerow([slug] + nums[-4:])
                        n += 1
                    break
    assert n == 6, f"Tabel 2.1 hanya {n}/6 baris"


def parse_komponen(pdf) -> None:
    import csv
    teks = pdf.pages[HAL_KOMPONEN].extract_text() or ""
    awal = teks.find("Uang Pendaftaran")
    akhir = teks.find("umber: Badan Pusat Statistik")
    seg = teks[awal:akhir].splitlines()
    hasil, toks = [], []
    untuk = 0
    for line in seg:
        nums = [a for k in re.findall(r"\d[\d\.,]*\d", line)
                for a in [angka_id(k)] if a is not None]
        if len(nums) >= 4:
            assert untuk < 16, f"baris angka berlebih: {line!r}"
            hasil.append((KOMPONEN_URUT[untuk], *nums[-4:]))
            untuk += 1
        elif len(nums) > 0:
            # baris angka tak lengkap: gabungkan sebagai kandidat
            found = False
            for i, t2 in enumerate(toks):
                combo = t2[1] + nums
                if len(combo) == 4:
                    hasil.append((KOMPONEN_URUT[untuk], *combo))
                    untuk += 1
                    toks.pop(i)
                    found = True
                    break
            if not found:
                toks.append((line, nums))
    assert len(hasil) == 16, f"komponen terparse {len(hasil)}/16"
    # aserti nilai per sel (firasat watermark) + jumlah kolom ~100
    for nama, a, b, c, d in hasil:
        exp = KOMPONEN_ASERTI[nama]
        got = (a, b, c, d)
        assert all(abs(x - y) < 0.011 for x, y in zip(exp, got)), \
            f"selisih pada {nama}: {got} vs {exp}"
    for j in range(1, 5):
        tot = sum(r[j] for r in hasil)
        assert abs(tot - 100) <= 0.2, f"jumlah kolom {j} = {tot}"
    with open(FOLDER / "data" / "spp-proporsi-komponen.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["komponen", "sd", "smp", "sma_smk", "pt"])
        w.writerows(hasil)
    print(f"komponen ter-parse: {len(hasil)} (jumlah kolom: "
          + ", ".join(f"{sum(r[j] for r in hasil):.2f}" for j in range(1, 5)) + ")")


def parse() -> None:
    with pdfplumber.open(PDF_PATH) as pdf:
        parse_total(pdf)
        parse_komponen(pdf)


if __name__ == "__main__":
    unduh()
    parse()
