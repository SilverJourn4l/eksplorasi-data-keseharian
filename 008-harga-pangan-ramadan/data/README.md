# Data Edisi 008: harga pangan mingguan sekitar Ramadan

## Sumber

**PIHPPS Nasional** (Pusat Informasi Harga Pangan Strategis Nasional,
bi.go.id/hargapangan), dikelola bersama Bank Indonesia dan Kementerian
Perdagangan: harga eceran 10 komoditas pangan strategis (beras, daging ayam,
daging sapi, telur ayam, bawang merah, bawang putih, cabai merah, cabai rawit,
minyak goreng, gula pasir) di pasar tradisional 34 provinsi tiap hari kerja,
beserta rerata nasional yang dihitung server. Kontrak endpoint sama dengan
Edisi 005/007 (`WebSite/Home/GetGridData1`, tiga header wajib browser). Tanggal
akses panen: 29 September 2026.

**Kalender Ramadan**: tanggal 1 Ramadan dan 1 Syawal versi ketetapan pemerintah
(sidag isbat Kementerian Agama), 2019-2026, dirangkum dari siaran resmi Kemenag
dan berita sidang isbat (ANTARA, Setneg, BBC). Muhammadiyah menetapkan awal
puasa berbeda satu-dua hari di sebagian tahun; edisi ini memakai tanggal
pemerintah, dengan catatan batas.

## Cara ambil

Delapan jendela Ramadan (2019/20 sampai 2025/26), masing-masing mulai 56 hari
sebelum 1 Ramadan dan selesai 42 hari setelah 1 Syawal. Satu snapshot per Rabu
per jendela per komoditas (sekarang ~1.500 permintaan); respons mentah disimpan
per berkas di `mentah/pihps/` (incremental). Bila tanggal yang diminta tidak
punya rilis baru, server membalas tanggal rilis terakhir; CSV dibangun dari
tanggal balasan server, jadi tanggal ganda hilang sendiri.

## Berkas

| Berkas | Isi |
|---|---|
| `tanggal-ramadan.csv` | 1 Ramadan & 1 Syawal pemerintah, 1440-1447 H |
| `harga-nasional-mingguan.csv` | `tanggal, komoditas, harga_nasional` (tanggal balasan server) |
| `harga-provinsi-mingguan.csv` | `tanggal, komoditas, provinsi, harga` |
| `mentah/pihps/` | Cache respons per Rabu-komoditas |
| `metrik-008.json` | Metrik temuan yang dicetak notebook (bootstrap 10.000 ulang, seed 2026) |

## Hal yang perlu digarisbawahi saat memakai ulang

1. **Rilis bergeser dan kesenjangan upstream.** Sembilan bulan di rentang
   2019-2023 sama sekali kosong di server (via Edisi 007; 2019-06, 2020-02,
   2020-08, 2020-11, 2021-05, 2021-08, 2022-01, 2022-05, 2023-07). Di
   minggu-minggu kosong itu server membalas rilis sebelumnya, sehingga kurva
   bertangga-datar di segmen tersebut; itu bukan artinya harga benar-benar diam,
   dan segmen terganggu 2021/2022 berada tepat di fase pasca-Lebaran.
2. **Nasional = rerata provinsi** dihitung server, bukan rerata tertimbang
   populasi pengkonsumsiannya.
3. **Pasar tradisional saja**, bukan harga di ritel modern atau grosir; tidak
   mencakup komoditas di luar sepuluh bahan ini.