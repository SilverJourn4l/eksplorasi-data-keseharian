"""
Pelabelan stance judul berita Edisi 004 (lihat data/protokol-labeling.md).

Klasifikasi primer deterministik berbasis leksikon terbuka, sesuai janji
reproduktibilitas jurnal: siapa pun yang menjalankan skrip ini atas data yang
sama mendapat label yang sama persis. Leksikon ini hasil revisi pasca-audit
ronde 1 (kesepakatan di bawah ambang 80 persen), lalu diaudit ulang.

Jalankan: python3 label_stance.py
"""

from pathlib import Path

import numpy as np
import pandas as pd


# --- Leksikon (revisi pasca-audit ronde 1) -------------------------------
MENOLAK_FRASA = [
    "menolak keras", "gelombang penolakan", "banjir kritik", "menuai kritik",
    "ramai dikritik", "menuai kecaman", "potensi kerusakan", "berpotensi merusak",
    "berpotensi mengancam", "potensi bencana", "dampak negatif", "dampak buruk",
    "dosa ekologis", "langkah mundur", "akal-akalan", "tipu-tipu", "tipu tipu",
    "harus dibatalkan", "greenwashing", "berkedok", "jual negara",
    "menjual negara", "jual tanah air", "kepentingan investor",
    "kepentingan asing", "tindak tegas", "efek jera", "ikut bermain",
    "diduga bermain", "ingkar janji", "minta dihapus", "kaji ulang",
    "desak pencabutan", "minta presiden cabut", "tuntut cabut",
    "minta dicabut", "minta ditunda", "ingatkan dampak", "ingatkan potensi",
    "tak mau ada tambang", "tidak mau tambang", "konflik kepentingan",
    "menjarah", "dijarah", "penjarahan", "cabut dan batalkan",
    "serukan pencabutan", "tak belajar dari", "tidak belajar dari",
    "pelanggaran ham", "sejarah peradilan", "negara terlalu lemah",
]
MENOLAK_KATA = [
    "tolak", "nolak", "kecam", "kritik", "protes", "unjuk rasa", "demonstrasi",
    "gugat", "uji materi", "nentang", "rusak", "ancam", "tenggelam",
    "abrasi", "banjir rob", "korban", "rugi", "bahaya", "khawatir", "resah",
    "was-was", "keberatan", "keluh", "lawan", "sorot", "kuno", "sesat",
    "mudarat", "madarat", "pusaran", "kikis", "desak", "tuntut", "stop",
    "moratorium", "haram", "gerus", "dihapus", "tunda", "buruk", "derita",
    "punah", "amblas", "dicaci", "waras",
]
# Istilah hukum/keuangan yang membatalkan sinyal kata tertentu.
MENOLAK_PENGECUALIAN = ["kerugian negara", "tidak haram", "tak haram"]
# Konteks sidang pidana bukan pernyataan sikap atas pengerukan.
KONTEKS_SIDANG = ["terdakwa", "eksepsi", "tipikor", "vonis", "divonis"]

MENDUKUNG_FRASA = [
    "menyambut baik", "disambut baik", "tidak merusak", "tak merusak",
    "dipastikan aman", "aman untuk", "klaim aman", "membawa manfaat",
    "peluang ekonomi", "penerimaan negara", "potensi ekonomi",
    "potensi penerimaan", "potensi keuntungan", "perlu dikeruk",
    "harus dikeruk",
]
MENDUKUNG_KATA = [
    "dukung", "apresiasi", "puji", "yakin", "jamin", "bermanfaat",
    "menguntungkan", "keuntungan", "pnbp", "optimistis", "solusi",
]
MENDUKUNG_FRASA += ["tak rusak", "tidak rusak"]
# Konteks yang membatalkan sinyal mendukung (mis. mengecilkan manfaat).
MENDUKUNG_PENGECUALIAN = ["sangat kecil"]

RELEVAN_FRASA = [
    "pasir laut", "sedimentasi laut", "sedimen laut", "sedimen di laut",
    "hasil sedimentasi", "ekspor pasir", "tambang pasir", "penambangan pasir",
    "pengerukan pasir", "keruk pasir", "kapal isap", "kapal keruk",
    "penyedot pasir", "curi pasir", "pencurian pasir", "pasir ilegal",
]

EPISODE = [
    ("E0_sebelum_pp", "2022-01-01", "2023-05-14"),
    ("E1_pp_disahkan", "2023-05-15", "2023-12-31"),
    ("E2_aturan_persiapan", "2024-01-01", "2024-08-28"),
    ("E3_ekspor_dibuka", "2024-08-29", "2025-06-01"),
    ("E4_pasca_putusan_ma", "2025-06-02", "2026-09-22"),
]


def normalisasi(teks):
    t = teks.lower().replace("ijin", "izin")
    t = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in t)
    return " ".join(t.split())


def relevan_judul(teks):
    t = " " + normalisasi(teks) + " "
    if ("timah" in t or "besi" in t) and "pasir laut" not in t and "sedimen" not in t:
        return False
    return any(p in t for p in RELEVAN_FRASA)


def label_judul(teks):
    t = " " + normalisasi(teks) + " "
    tolak = sum(t.count(f" {p} ") for p in MENOLAK_FRASA)
    dukung = sum(t.count(f" {p} ") for p in MENDUKUNG_FRASA)
    rusak_dinegasikan = "tak rusak" in t or "tidak rusak" in t
    for token in t.split():
        for k in MENOLAK_KATA:
            if k in token:
                if k == "rusak" and rusak_dinegasikan:
                    continue
                if k == "haram" and any(p in t for p in ("tidak haram", "tak haram")):
                    continue
                tolak += 1
        for k in MENDUKUNG_KATA:
            if k in token:
                dukung += 1
    if "kerugian negara" in t:
        n_rugi = sum(1 for token in t.split() if "rugi" in token)
        tolak = max(tolak - n_rugi, 0)
    if any(p in t for p in MENDUKUNG_PENGECUALIAN):
        dukung = max(dukung - 1, 0)
    # Aturan tanya: kalimat tanya tanpa sinyal menolak bukanlah dukungan.
    if "?" in teks and dukung > 0 and tolak == 0:
        dukung = 0
    # Konteks sidang pidana: bukan pernyataan sikap atas pengerukan.
    if any(k in t for k in KONTEKS_SIDANG):
        tolak, dukung = 0, 0
    if tolak > 0 and dukung > 0:
        return "campuran", tolak, dukung
    if tolak > 0:
        return "menolak", tolak, dukung
    if dukung > 0:
        return "mendukung", tolak, dukung
    return "netral", 0, 0


def utama():
    df = pd.read_csv(FOLDER / "data" / "berita-pasir-laut.csv", parse_dates=["tanggal"])
    df["relevan"] = df["judul"].map(lambda x: relevan_judul(str(x)))
    hasil = df["judul"].map(lambda x: label_judul(str(x)))
    df["label"] = [h[0] for h in hasil]
    df.loc[~df["relevan"], "label"] = "di_luar_topik"
    df["n_tolak"] = [h[1] for h in hasil]
    df["n_dukung"] = [h[2] for h in hasil]

    tanggal = df["tanggal"].dt.date.astype(str)
    df["episode"] = "di_luar_jendela"
    for nama, a, b in EPISODE:
        df.loc[(tanggal >= a) & (tanggal <= b), "episode"] = nama

    keluaran = FOLDER / "data" / "berita-berlabel.csv"
    df.to_csv(keluaran, index=False)
    print("Ringkasan label:")
    print(df["label"].value_counts().to_string())
    print(f"\nRelevan: {int(df['relevan'].sum())} | di luar topik: {int((~df['relevan']).sum())}")
    sub = df[df["relevan"]]
    print("\nKomposisi per episode atas judul relevan (proporsi):")
    tabel = pd.crosstab(sub["episode"], sub["label"], normalize="index").round(3)
    print(tabel.to_string())
    print(f"\nTersimpan: {keluaran}")


def sampel_audit(n=200, seed=42):
    """Sampel acak berstrata proporsional per episode untuk audit manual."""
    df = pd.read_csv(FOLDER / "data" / "berita-berlabel.csv", parse_dates=["tanggal"])
    df = df[df["relevan"]]
    rng = np.random.default_rng(seed)
    bagian, alokasi = [], {}
    for ep, sub in df.groupby("episode"):
        k = max(1, round(n * len(sub) / len(df)))
        alokasi[ep] = k
        bagian.append(sub.sample(n=min(k, len(sub)), random_state=int(rng.integers(2**31))))
    sampel = pd.concat(bagian).sample(frac=1, random_state=seed)
    keluaran = FOLDER / "data" / "audit-labeling.csv"
    sampel[["judul", "sumber", "tanggal", "episode", "label"]].rename(
        columns={"label": "label_leksikon"}
    ).assign(label_audit="").to_csv(keluaran, index=False)
    print(f"Sampel audit {len(sampel)} judul tersimpan: {keluaran}")
    print("Alokasi per episode:", alokasi)


if __name__ == "__main__":
    utama()
    sampel_audit()
