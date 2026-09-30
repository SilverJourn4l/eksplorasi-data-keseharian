"""Unduh tabel provinsi dari Wikipedia Indonesia (rujukan: BPS) untuk Edisi 003 dan susun data olahan.

Sumber: Wikipedia bahasa Indonesia (CC BY-SA), tabel PDRB per kapita 2021, IPM 2021/2024/2025,
dan master wilayah. BPS langsung tidak bisa diakses otomatis (403), tercatat di README edisi.
Setiap respons JSON disimpan apa adanya di data/mentah supaya hasil parse bisa diaudit ulang.
"""

import json
import re
import unicodedata
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

UA = {"User-Agent": "JurnalDataKeseharian/1.0 (jurnal edukasi; kontak: pengelola@example.com)"}
API = "https://id.wikipedia.org/w/api.php"
MENTAH = Path("data/mentah")

HALAMAN = {
    "ipm": "Daftar provinsi Indonesia menurut IPM",
    "pdrb": "Daftar provinsi di Indonesia menurut PDRB",
    "provinsi": "Provinsi di Indonesia",
}

# Kurs tengah BI rata-rata 2021 ~14.250 Rp/US$. Dipakai untuk memvalidasi parse skala
# PDRB per kapita, bukan sebagai data baru.
FX_2021_MIN, FX_2021_MAX = 13000, 15500


def fetch_parse(title):
    resp = requests.get(
        API,
        params={"action": "parse", "page": title, "prop": "text", "format": "json", "redirects": "1"},
        headers=UA,
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    if "error" in body:
        raise RuntimeError(f"{title}: {body['error'].get('info')}")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    MENTAH.mkdir(parents=True, exist_ok=True)
    (MENTAH / f"{slug}.json").write_text(
        json.dumps({"judul": title, "diakses_utc": datetime.now(timezone.utc).isoformat(), "respons": body},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return pd.read_html(StringIO(body["parse"]["text"]["*"]))


def bersih(x):
    s = unicodedata.normalize("NFKC", str(x))
    s = s.replace("\u200b", "").strip()
    return re.sub(r"\[\d+\]|\[catatan \d+\]", "", s).strip()


def parse_skala_100(x):
    """Nilai tabel wiki yang koma desimalnya tertelan: "8505" -> 85.05, "090" -> 0.90."""
    s = bersih(x).replace("%", "").replace(".", "").replace(",", ".")
    if re.fullmatch(r"-?\d+", s):
        return int(s) / 100
    return float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s) else None


def parse_ribuan(x):
    """Angka bergaya Indonesia: "19.199" -> 19199, "23.625,5" -> 23625.5."""
    s = bersih(x).replace(".", "").replace(",", ".")
    return float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s) else None


def parse_pdrb_juta(x, usd):
    """PDRB per kapita juta rupiah: pilih skala yang membuat kurs 2021 masuk akal."""
    s = bersih(x).replace(".", "").replace(",", ".")
    if not re.fullmatch(r"-?\d+", s) or not usd:
        return None
    mentah_int = int(s)
    for kandidat in (mentah_int / 100, mentah_int / 10, float(mentah_int)):
        if usd > 0 and FX_2021_MIN <= kandidat * 1_000_000 / usd <= FX_2021_MAX:
            return kandidat
    return None


ALIAS_NAMA = {"kepulauan bangka belitung": "bangka belitung"}


def kunci_nama(x):
    s = bersih(x).lower()
    s = re.sub(r"\b(daerah khusus ibukota|daerah khusus|daerah istimewa|provinsi|nanggroe aceh darussalam)\b", " ", s)
    s = re.sub(r"[^a-z ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # "Kepulauan Riau" beda provinsi dengan "Riau"; hanya "Kepulauan Bangka Belitung" yang disingkatkan
    return ALIAS_NAMA.get(s, s)


def ambil_ipm():
    semua = []
    for tabel in fetch_parse(HALAMAN["ipm"]):
        if tabel.shape[1] < 5 or tabel.shape[0] < 30:
            continue
        thn_match = re.search(r"\('Peringkat', '(\d{4})", str(tabel.columns[0]))
        if not thn_match:
            continue
        tahun = int(thn_match.group(1))
        if tahun not in (2021, 2024, 2025):
            continue
        baris = []
        for _, r in tabel.iterrows():
            if not re.fullmatch(r"\d+", bersih(r.iloc[0]).replace(".", "")):
                continue
            ipm = parse_skala_100(r.iloc[3])
            if ipm is None or not 50 <= ipm <= 95:
                continue
            baris.append({"provinsi": bersih(r.iloc[2]), "ipm": ipm})
        if not baris:
            continue
        df = pd.DataFrame(baris)
        df["tahun"] = tahun
        df["kunci"] = df["provinsi"].map(kunci_nama)
        df = df.drop_duplicates("kunci", keep="first")
        semua.append(df)
        df.to_csv(MENTAH / f"ipm-{tahun}.csv", index=False)
    return pd.concat(semua, ignore_index=True)


def ambil_pdrb():
    tabel = next(
        t for t in fetch_parse(HALAMAN["pdrb"])
        if t.shape[0] > 30 and any("per kapita" in str(c).lower() for c in t.columns)
    )
    # tabel per kapita 2021: 0 peringkat, 1 provinsi, 2 juta rupiah, 3 US$, 4 negara pembanding
    baris = []
    for _, r in tabel.iterrows():
        nama = bersih(r.iloc[1])
        if not nama or not re.fullmatch(r"\d+", bersih(r.iloc[0]).replace(".", "")):
            continue
        usd = parse_ribuan(r.iloc[3])
        juta = parse_pdrb_juta(r.iloc[2], usd)
        baris.append({"provinsi": nama, "kunci": kunci_nama(nama),
                      "pdrb_kapita_juta_2021": juta, "pdrb_kapita_usd_2021": usd})
    df = pd.DataFrame(baris).dropna(subset=["pdrb_kapita_juta_2021"]).drop_duplicates("kunci")
    df.to_csv(MENTAH / "pdrb-kapita-2021.csv", index=False)
    return df


def ambil_master():
    tabel = next(t for t in fetch_parse(HALAMAN["provinsi"]) if t.shape[1] >= 8 and t.shape[0] >= 30)
    cols = [str(c) for c in tabel.columns]
    (MENTAH / "kolom-master.txt").write_text("\n".join(cols), encoding="utf-8")
    idx_wil = next(i for i, c in enumerate(cols) if "geografis" in c.lower())
    baris = [{"provinsi": bersih(r.iloc[1]), "kunci": kunci_nama(r.iloc[1]),
              "wilayah_geografis": bersih(r.iloc[idx_wil])} for _, r in tabel.iterrows()]
    df = pd.DataFrame(baris).dropna(subset=["kunci"]).drop_duplicates("kunci")
    df["jawa"] = (df.wilayah_geografis.str.lower().str.contains("jawa")
                  & ~df.wilayah_geografis.str.lower().str.contains("non"))
    df.to_csv(MENTAH / "master-provinsi.csv", index=False)
    return df


def gabung(ipm, pdrb, master):
    out = (
        ipm[ipm.tahun == 2021][["provinsi", "kunci"]]
        .merge(pdrb[["kunci", "pdrb_kapita_juta_2021", "pdrb_kapita_usd_2021"]], on="kunci", how="left")
        .merge(master[["kunci", "wilayah_geografis", "jawa"]], on="kunci", how="left")
    )
    for tahun in (2021, 2024, 2025):
        kolom = ipm[ipm.tahun == tahun].set_index("kunci")["ipm"].rename(f"ipm_{tahun}")
        out = out.merge(kolom, on="kunci", how="left")
    return out


def lapor(gab, ipm, pdrb, master):
    print("ipm per tahun (baris):", dict(ipm.groupby("tahun").size()))
    print("pdrb valid:", len(pdrb), "| master:", len(master))
    print("gabungan:", len(gab), "| lengkap pdrb+ipm2021:",
          int(gab.dropna(subset=["pdrb_kapita_juta_2021", "ipm_2021"]).shape[0]))
    tanpa_pdrb = gab[gab.pdrb_kapita_juta_2021.isna()].provinsi.tolist()
    print("tanpa PDRB per kapita:", tanpa_pdrb)
    tanpa_master = gab[gab.wilayah_geografis.isna()].provinsi.tolist()
    print("tanpa wilayah:", tanpa_master)
    cek = gab.dropna(subset=["pdrb_kapita_juta_2021", "pdrb_kapita_usd_2021"])
    fx = cek.pdrb_kapita_juta_2021 * 1_000_000 / cek.pdrb_kapita_usd_2021
    print(f"implied fx 2021: min={fx.min():.0f} max={fx.max():.0f} (harus ~14.250)")


def main():
    ipm = ambil_ipm()
    pdrb = ambil_pdrb()
    master = ambil_master()
    gab = gabung(ipm, pdrb, master)
    gab.to_csv("data/provinsi.csv", index=False)
    lapor(gab, ipm, pdrb, master)
    print("\ncontoh 5 baris:")
    print(gab.head().to_string())


if __name__ == "__main__":
    main()
