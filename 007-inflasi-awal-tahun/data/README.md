# Data Edisi 007: inflasi awal tahun

## Sumber

**Lapis A (indeks resmi):** Data CPI bulanan Indonesia (sumber nasional BPS)
yang direlay OECD (statistik resmi, diunduh lewat API SDMX OECD tanpa kunci),
2015 s.d. Agustus 2026, 140 bulan, dua seri: indeks (IHK umum) dan pertumbuhan
tahunan. Catatan jujur: katalog BPS langsung tidak dapat diakses dari lingkungan
panen ini (tabel web BPS membalas 403 dan API BPS minta token), jadi dipakai
relay resmi OECD; angka berasal dari BPS.

**Lapis B (harga keseharian):** PIHPPS Nasional (bi.go.id/hargapangan), dikelola
bersama Bank Indonesia dan Kementerian Perdagangan: harga eceran 10 komoditas
pangan strategis (beras, daging ayam, daging sapi, telur ayam, bawang merah,
bawang putih, cabai merah, cabai rawit, minyak goreng, gula pasir), rerata
nasional dan 34 provinsi per hari kerja. Kontrak endpoint sama dengan Edisi 005
(`WebSite/Home/GetGridData1`, tiga header wajib); satu snapshot tanggal
pertengahan per bulan, Oktober 2018 sampai Agustus 2026. Tanggal akses panen:
29 September 2026.

## Berkas

| Berkas | Isi |
|---|---|
| `mentah/oecd/cpi-idn-*.csv` | Seri CPI bulanan (indeks dan YoY), unduhan SDMX OECD |
| `harga-nasional-bulanan.csv` | `tanggal, komoditas, harga_nasional` (tanggal rilis balasan server) |
| `harga-provinsi-bulanan.csv` | `tanggal, komoditas, provinsi, harga` |
| `mentah/pihps/` | Cache respons mentah per bulan-komoditas (incremental) |
| `metrik-007.json` | Metrik temuan yang dicetak notebook (bootstrap 10.000 ulang, seed 2026) |

## Hal yang perlu digarisbawahi saat memakai ulang

1. **Dua lapis sengaja dipisah.** IHK resmi menghitung ratusan barang-jasa
   tertimbang pengeluaran; PIHPS hanya memantau 10 komoditas pangan pasar
   tradisional. Keduanya dibaca berdampingan, tidak digabung satu angka.
2. **Rilis bergeser.** Tanggal diminta adalah pertengahan bulan; server
   membalas tanggal rilis terdekat, dan CSV dibangun dari tanggal balasan.
   Transisi "awal tahun" dibaca sebagai perubahan Desember-pertengahan ke
   Januari-pertengahan.
3. **Sembilan bulan kosong dari server.** Sembilan bulan (2019-06, 2020-02,
   2020-08, 2020-11, 2021-05, 2021-08, 2022-01, 2022-05, 2023-07) membalas
   kosong untuk kesepuluh komoditas (kesenjangan upstream, bukan kegagalan
   panen). Januari 2022 termasuk di dalamnya, sehingga ramp awal tahun dibaca
   dari tujuh Januari (2019-2021, 2023-2026), bukan delapan.
4. **Nasional = rerata provinsi** yang dihitung server, bukan rerata tertimbang
   populasi; perubahan nasional kecil bisa membalik tanda bila provinsi yang
   berkontras besar.
5. **Komponen IHK resmi.** Pembacaan "siapa yang naik" di lapisan resmi
   (komponen IHK) memerlukan data BPS yang aksesnya tertutup dari lingkungan
   panen ini; pembacaan komponen di edisi ini digantikan keranjang dapur PIHPS
   yang kontraknya terbuka.
