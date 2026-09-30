"""
Pengayaan data Edisi 004: mengambil isi artikel dari tautan agregator.

Satuan analisis edisi ini tetap JUDUL berita. Skrip ini lapisan tambahan:
menjernihkan tautan redirect Google News ke URL penerbit asli, lalu mengunduh
halaman artikelnya sekali per URL. Berguna untuk mengecek konteks di balik
judul, misalnya saat menyusun tabel insiden atau mengaudit leksikon.

Cara kerja:
1. Resolve tautan Google News lewat endpoint internal batchexecute (Fbv4je).
   Jika Google mengubah protokolnya, baris itu tercatat gagal-resolve dan
   analisis utama edisi tidak terdampak sama sekali.
2. Unduh halaman artikel sekali, cache di data/mentah/teks/, sehingga
   menjalankan ulang tidak mengunduh ulang.
3. Ekstrak isi: pakai trafilatura bila terpasang; jika tidak, fallback
   BeautifulSoup (JSON-LD articleBody, kontainer <article>/kelas umum,
   lalu paragraf panjang setelah menu dan elemen navigasi dibuang).

Batasan jujur:
- Hasil skrip ini (data/hasil-scrape.csv, cache resolve, cache teks di
  data/mentah/) bersifat lokal dan tidak ikut terbit di repo. Isi artikel
  adalah milik penerbitnya; yang disebarluaskan tetap cukup judul.
- Sebagian media besar memblokir pengunduh otomatis (HTTP 202/403); baris
  seperti itu tercatat "diblokir" apa adanya, tanpa upaya menghindar.
- Permintaan dijadwalkan pelan (jeda antar-baris, satu permintaan dalam satu
  waktu, tanpa retry agresif) supaya beban ke server penerbit minimal.

Jalankan: python3 scrape_artikel.py
Contoh:   python3 scrape_artikel.py --acak 20 --seed 42   # uji cepat sampel
"""

import json
import re
import time
import random
import argparse
from hashlib import md5
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

FOLDER = Path(__file__).parent
MASUKAN = FOLDER / "data" / "berita-pasir-laut.csv"
HASIL = FOLDER / "data" / "hasil-scrape.csv"
MENTAH = FOLDER / "data" / "mentah"
RESOLVE_JSON = MENTAH / "resolve.json"          # peta tautan_gnews -> url asli
FOLDER_TEKS = MENTAH / "teks"                   # cache isi artikel (di-gitignore)
JEDA = 1.8
TIMEOUT = 20

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"}
URL_BATCH = "https://news.google.com/_/DotsSplashUi/data/batchexecute?rpcids=Fbv4je"

BUANG_TAG = (
    "script", "style", "nav", "header", "footer", "aside", "form", "noscript",
    "figure", "figcaption", "ul", "ol", "table", "iframe", "button", "select",
    "input", "svg",
)
BUANG_KATA = (
    "baca juga", "saksikan", "tonton juga", "ikuti kami", "simak breaking",
    "advertisement", "powered by", "copyright",
)
KELAS_ISI = (
    "entry-content", "post-content", "article-content", "articlebody",
    "article-body", "detail-konten", "content-news", "read__content",
    "text-detail", "article_body", "isi-berita", "content-detail",
    "td-post-content", "detail__body-text", "text__detail", "body-konten",
)

try:  # opsional: ekstraktor pihak ketiga yang lebih matang
    import trafilatura  # type: ignore
except ImportError:
    trafilatura = None


def kunci(tautan):
    return md5(tautan.encode("utf-8")).hexdigest()


def muat_resolve():
    if RESOLVE_JSON.exists():
        return json.loads(RESOLVE_JSON.read_text())
    return {}


def simpan_resolve(peta):
    RESOLVE_JSON.write_text(json.dumps(peta, indent=1, ensure_ascii=False))


def resolve_gnews(tautan, sesi):
    """Kembalikan URL penerbit asli, atau None bila tidak berhasil."""
    cocok = re.search(r"/articles/([^?]+)", tautan)
    if not cocok:
        return None
    gnid = cocok.group(1)
    p = sesi.get(tautan, headers=UA, timeout=TIMEOUT)
    sig = re.search(r'data-n-a-sg="([^"]+)"', p.text)
    ts = re.search(r'data-n-a-ts="([^"]+)"', p.text)
    if not (sig and ts):
        return None
    req = [
        "garturlreq",
        [["id", "ID", ["FINANCE_TOP_INDICES", "WEB_TEST_1_0_0"], None, None, 1, 1,
          "ID:id", None, 180, None, None, None, None, None, 0, None, None,
          [1608992183, 723341000]], "id", "ID", 1, [2, 3, 4, 8], 1, 0,
         "655000234", 0, 0, None, 0],
        gnid, int(ts.group(1)), sig.group(1),
    ]
    payload = "f.req=" + json.dumps([[["Fbv4je", json.dumps(req, separators=(",", ":")), None, "generic"]]])
    r = sesi.post(URL_BATCH, headers={**UA,
                  "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                  "Referer": "https://news.google.com/"},
                  data=payload, timeout=TIMEOUT)
    m = re.search(r'garturlres\\",\\"(https?://[^"\\]+)', r.text)
    return m.group(1) if m else None


def bersihkan(t):
    return re.sub(r"\s+", " ", t or "").strip()


def dari_jsonld(sup):
    for s in sup.find_all("script", {"type": "application/ld+json"}):
        try:
            d = json.loads(s.string or "")
        except Exception:
            continue
        if isinstance(d, dict) and "@graph" in d:
            items = d["@graph"]
        elif isinstance(d, list):
            items = d
        else:
            items = [d]
        for it in items:
            if isinstance(it, dict) and it.get("articleBody"):
                return bersihkan(it["articleBody"])
    return None


def dari_container(sup):
    kandidat = sup.find("article")
    if kandidat is None:
        for el in sup.find_all(True):
            atribut = " ".join([str(el.get("class", "")), str(el.get("id", ""))]).lower()
            if any(k.lower() in atribut for k in KELAS_ISI):
                kandidat = el
                break
    lingkup = kandidat if kandidat is not None else (sup.body or sup)
    paragraf = []
    for p in lingkup.find_all("p"):
        t = bersihkan(p.get_text(" "))
        if len(t) < 60:
            continue
        if any(k in t.lower() for k in BUANG_KATA):
            continue
        paragraf.append(t)
    return " ".join(paragraf) if paragraf else None


def ekstrak(html):
    if trafilatura is not None:
        t = trafilatura.extract(html)
        if t and len(t) > 200:
            return bersihkan(t), "trafilatura"
    sup = BeautifulSoup(html, "lxml")
    for tag in sup(BUANG_TAG):
        tag.decompose()
    t = dari_jsonld(sup)
    if t and len(t) > 200:
        return t, "jsonld"
    return dari_container(sup), "container"


def unduh_dan_ekstrak(url_asli, berkas, sesi):
    """Ambil halaman artikel sekali; hasil dicache di berkas JSON lokal."""
    if berkas.exists():
        return json.loads(berkas.read_text())
    for upaya in (1, 2):
        try:
            resp = sesi.get(url_asli, headers=UA, timeout=TIMEOUT)
            if resp.status_code != 200:
                # misal 202/403: perlindungan anti-bot penerbit; jangan dipaksa
                hasil = {"url_asli": url_asli, "status": "diblokir", "via": "",
                         "kode_http": resp.status_code, "n_karakter": 0, "teks": ""}
            else:
                teks, via = ekstrak(resp.text)
                status = "ok" if (teks and len(teks) >= 200) else "kosong"
                hasil = {"url_asli": url_asli, "status": status, "via": via,
                         "kode_http": resp.status_code, "n_karakter": len(teks or ""),
                         "teks": teks or ""}
            if hasil["status"] == "ok":  # hanya cache berhasil, sisanya coba lagi lain waktu
                berkas.write_text(json.dumps(hasil, ensure_ascii=False))
            return hasil
        except requests.RequestException:
            if upaya == 2:
                return {"url_asli": url_asli, "status": "gagal-unduh", "via": "",
                        "kode_http": 0, "n_karakter": 0, "teks": ""}
            time.sleep(5)
    raise AssertionError("tidak terjangkau")


def main():
    ap = argparse.ArgumentParser(description="Pengayaan isi artikel Edisi 004")
    ap.add_argument("--masukan", default=str(MASUKAN), help="CSV sumber (kolom: judul,sumber,tanggal,tautan)")
    ap.add_argument("--acak", type=int, default=0, help="ambil sampel acak N baris (butuh --seed)")
    ap.add_argument("--seed", type=int, default=42, help="seed sampler acak, default 42")
    ap.add_argument("--jeda", type=float, default=JEDA, help="jeda sopan antar-baris, detik")
    args = ap.parse_args()

    FOLDER_TEKS.mkdir(parents=True, exist_ok=True)
    masukan = Path(args.masukan)
    df = pd.read_csv(masukan)
    if args.acak:
        rng = random.Random(args.seed)
        df = df.iloc[rng.sample(range(len(df)), min(args.acak, len(df)))].sort_index()

    peta = muat_resolve()
    sesi = requests.Session()
    baris = []
    for i, r in df.iterrows():
        tautan = r["tautan"]
        nama = FOLDER_TEKS / f"{kunci(tautan)}.json"
        if nama.exists():  # teks pernah terunduh: pakai cache, tanpa jaringan
            hasil = json.loads(nama.read_text())
            baris.append({**r, "tautan_asli": hasil["url_asli"],
                          "status": hasil["status"], "via": hasil["via"],
                          "kode_http": hasil.get("kode_http", 200),
                          "n_karakter": hasil["n_karakter"]})
            print(f"[{len(baris)}/{len(df)}] {r['sumber']}: {hasil['status']} (cache)")
            continue
        asli = peta.get(tautan)
        if asli is None:
            try:
                asli = resolve_gnews(tautan, sesi)
            except requests.RequestException:
                asli = None
            if asli:
                peta[tautan] = asli
                simpan_resolve(peta)
            time.sleep(args.jeda)
        if not asli:
            baris.append({**r, "tautan_asli": "", "status": "gagal-resolve",
                          "via": "", "kode_http": 0, "n_karakter": 0})
            continue
        hasil = unduh_dan_ekstrak(asli, nama, sesi)
        baris.append({**r, "tautan_asli": asli, "status": hasil["status"],
                      "via": hasil["via"], "kode_http": hasil["kode_http"],
                      "n_karakter": hasil["n_karakter"]})
        print(f"[{len(baris)}/{len(df)}] {r['sumber']}: {hasil['status']}")
        time.sleep(args.jeda)

    keluaran = pd.DataFrame(baris)
    keluaran.to_csv(HASIL, index=False)
    ringkas = keluaran["status"].value_counts().to_dict()
    print(f"\nSelesai: {len(keluaran)} baris -> {HASIL.relative_to(FOLDER)}")
    print(f"Status: {ringkas}")
    ok = keluaran[keluaran["status"] == "ok"]
    if len(ok):
        print(f"Panjang teks ok: median {int(ok['n_karakter'].median())} karakter")


if __name__ == "__main__":
    main()
