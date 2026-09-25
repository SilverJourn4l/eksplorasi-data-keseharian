# Data Edisi 005: harga pangan harian PIHPPS

## Sumber

**PIHPPS Nasional** (Pusat Informasi Harga Pangan Strategis Nasional),
<https://www.bi.go.id/hargapangan>, dikelola bersama Bank Indonesia dan Kementerian
Perdagangan. Setiap hari kerja, enumerator mencatat harga eceran komoditas pangan
strategis di pasar tradisional per provinsi; situs menayangkan rata-rata provinsi
sekaligus rata-rata nasionalnya. Tanggal akses panen: 22-23 September 2026.

## Cara ambil

Titik unduh: `https://www.bi.go.id/hargapangan/WebSite/Home/GetGridData1`
(didokumentasikan publik sebagai kontrak terbuka; tiga header wajib)
dengan parameter tanggal, komoditas, dan jenis harga pasar tradisional
(`priceType=1`). Satu permintaan membalas satu snapshot: 34 baris provinsi
plus nilai nasional yang dihitung server. Skrip [`../unduh_data.py`](../unduh_data.py)
meminta satu tanggal hari kerja per komoditas per musim dan menyimpan respons
mentah di `mentah/pihps/` (`{komoditas}_{tanggal-diminta}.json`).

## Berkas

| Berkas | Isi |
|---|---|
| `harga-nasional.csv` | `tanggal, komoditas, harga_nasional` (Rp/kg, rerata server antar-provinsi) |
| `harga-provinsi.csv` | `tanggal, komoditas, provinsi, harga` (Rp/kg) |
| `metrik-005.json` | Metrik temuan yang dicetak notebook (bootstrap 10.000 ulang, seed 2026) |
| `mentah/pihps/` | Cache respons mentah per tanggal (incremental) |

Cakupan: 4 komoditas (cabai merah, cabai rawit, bawang merah, beras), 7 musim
Nataru (Sep-Mar 2019/20 s.d. 2025/26), hari kerja.

## Hal yang perlu digarisbawahi saat memakai ulang

1. **Rilis bergeser.** Bila diminta tanggal tanpa rilis baru, server membalas
   "tanggal rilis terakhir". Skrip menyimpan tanggal balasan dan CSV dibangun
   dari tanggal balasan, jadi baris ganda hilang sendiri; konsekuensinya ada
   hari kosong, terutama akhir pekan (Sabtu-Minggu tidak diambil).
2. **Nasional = rerata provinsi.** `harga_nasional` adalah rata-rata
   antar-provinsi yang dihitung server, bukan rerata tertimbang populasi.
   Dipakai apa adanya dan dinyatakan begitu di tulisan.
3. **Provinsi baru.** Kepulauan Riau masuk survei belakangan; di snapshot awal
   barisnya ada tapi tanpa pembanding. Analisis hanya memakai kolom harga dan
   nasional, jadi ini tidak mengganggu deret.
4. **Jeda sopan.** Permintaan dijadwalkan 1,4 detik plus jitter, satu dalam
   satu waktu; skrip berhenti sendiri bila diblok berulang (403/429).
