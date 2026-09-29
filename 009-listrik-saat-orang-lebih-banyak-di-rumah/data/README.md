# Data edisi 009 — Listrik saat orang lebih banyak di rumah

## Sumber

Statistik PLN (buku tahunan resmi, ISSN 0852-8179):

- Statistik 2023: https://www.pln.co.id/webapi/media/file/webkorp/asset/Statistik2023.pdf
- Statistik 2024: https://www.pln.co.id/webapi/media/file/webkorp/asset/Statistik2024.pdf

Diunduh 29 September 2026. Keenam PDF mentah (2019-2024, ±41 MB) diarsipkan di
bundel git root workspace pada tag `edisi-009`; sengaja tidak disalin ke folder ini
agar workspace tetap ramping, dan bisa diregenerasi kapan pun lewat
`python3 ../unduh_data.py` (buku 2023 & 2024, dan pola URL yang sama untuk
2019-2022). Saat pengunduhan, Statistik 2025 belum terbit (URL pola yang sama
mengembalikan 404). Edisi 2021 gagal diunduh penuh (koneksi terputus dan server
menolak byte-range); tidak dipakai karena seluruh runtun 2015-2024 sudah
tertutupi oleh buku 2023 dan 2024.

## Tabel yang dipakai (bagian "Data Runtun Waktu")

- Energi Terjual per Kelompok Pelanggan (GWh/TWh) → `pln-terjual_gwh.csv`
- Energi Terjual Rata-rata per Kelompok Pelanggan (kWh) → `pln-rerata_kwh.csv`
- Jumlah Pelanggan per Kelompok Pelanggan → `pln-pelanggan.csv`

Kelompok pelanggan: rumah_tangga, industri, bisnis, sosial, gdg_pemerintah (gedung
kantor pemerintah), pju (penerangan jalan umum). Kolom "Jumlah/Total" dan "Lainnya"
di buku asli dibuang; total dihitung ulang bila diperlukan.

## Cara ekstrak

`unduh_data.py` (akarnya folder edisi ini): unduh PDF, parse teks dengan pdfplumber
(bukan OCR), potong segmen antara judul tabel target dan judul tabel berikutnya,
lalu cocokkan baris `tahun` + 6–10 token angka format Indonesia ("1.012.089,00").
Baris dengan kolom delta dalam kurung — seperti "(0,79)" pada 2020 — tetap dikenali.
Bila satu tahun muncul di dua buku, nilainya dirata-ratakan; selisih antarbuku
dicetak notebook sebagai metrik verifikasi (maks 0,01 satuan tabel).

## CSV

- `pln-terjual_gwh.csv` — penjualan energi per kelompok, GWh, 2015–2024
- `pln-rerata_kwh.csv` — energi terjual rata-rata per pelanggan, kWh, 2015–2024
- `pln-pelanggan.csv` — jumlah pelanggan per kelompok, pelanggan, 2015–2024
- `pln-ekstrak.json` — hasil parse mentah per buku (jejak audit)

Lisensi data: hak cipta tabel milik PT PLN (Persero); dipakai di sini untuk
kepentingan analisis dengan atribusi.
