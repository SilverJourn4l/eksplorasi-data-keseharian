# Data edisi 012: biaya masuk sekolah, dan semua yang menyertainya

## Sumber

- **BPS (2025), "Statistik Penunjang Pendidikan 2024"**, Katalog 4301007
  (ISBN 2622-8033), Jakarta, rilis 28 Mei 2025, 200 halaman. Isinya adalah
  hasil pengolahan **Susenas Modul Sosial Budaya dan Pendidikan (MSBP)**,
  modul yang digenggam setiap tiga tahun; data modul ini adalah
  **tahun ajaran 2023/2024**. PDF publikasi diambil dari laman publikasi
  resmi `bps.go.id` dan disimpan mentah di `mentah/spp-2024.pdf`
  (26.250.000 bita; sha256
  `d67a6f96e8ee9ac569a6bdf7c9ed13f90b92cf4bf88cc017b342a4740a5db3c2`).
  Alamat unduhan persisnya ada di `unduh_data.py` (token unduhan BPS dapat
  kedaluwarsa; bila gagal, ambil tautan baru dari halaman publikasi dan
  timpa berkas).

## Tabel yang diambil programatik (oleh `unduh_data.py`)

- **Tabel 2.1** (halaman cetak 15): rata-rata total biaya pendidikan per
  murid per tahun menurut karakteristik rumah tangga / wilayah kali jenjang
  (juta rupiah) menjadi `spp-total-karakteristik.csv` (6 baris x 4 jenjang).
- **Tabel 2.2** (halaman cetak 16): proporsi enam belas komponen biaya
  menurut jenjang (persen) menjadi `spp-proporsi-komponen.csv`
  (16 baris x 4 jenjang).

PDF aslinya membawa watermark diagonal yang hurufnya sesekali menempel pada
angka (misalnya "d0,58"), sehingga pembersihannya bukan pencocokan teks
melainkan urutan komponen yang diketahui, dan **tiap sel disahkan terhadap
salinan verifikasi manual** di dalam skrip; sebagai ganda-cek, jumlah tiap
kolom proporsi harus berada dalam selang 100 +/- 0,2 poin persen (terpenuhi:
99,98-100,02). Bila sahakan gagal, skrip berhenti dan tidak menulis CSV.

## Agregasi yang didefinisikan edisi ini (di notebook)

Lima kelompok komponen dari enam belas rincian Tabel 2.2:

1. **Awal tahun ajaran** = uang pendaftaran + baju sekolah dan
   perlengkapannya + buku pelajaran + LKS + alat tulis;
2. **Iuran dan kegiatan sekolah** = SPP/UKT + komite + ekstrakurikuler +
   praktikum + kursus sekolah + evaluasi/ujian + study tour + pendukung
   pembelajaran;
3. **Uang saku**; 4. **Uang transpor**; 5. **Lainnya**.

Terjemahan ke rupiah dihitung sebagai porsi komponen dikali total Tabel 2.1
per jenjang; perkalian ini meniru cara publikasi membaca tabel-tabelnya
sendiri dan diperlakukan sebagai taksiran rupiah atas rerata nasional, bukan
pengeluaran individual tertentu.

## Hal yang tidak tersedia di berkas ini (sengaja)

- Publikasi menyediakan galat sampel pada Tabel 2.13 s.d. 2.16 untuk rancangan
  sampelnya; edisi ini mengutip keberadaannya dan tidak menghitung ulang
  karena data mikro tidak dipakai. Kesimpulan utama bekerja pada orde faktor
  (selisih 2-2,7 kali lipat antar kelompok pengeluaran) yang jauh di atas
  galat sampel tipikal tabel-tabel ini.
- Rincian negeri vs swasta dan kabupaten/kota tersedia pada tabel lain
  publikasi yang sama; edisi ini memakai potongan nasional per jenjang.

Lisensi data: publikasi pemerintah dikutip untuk analisis dengan atribusi;
berkas mentah disimpan lokal untuk reproducibility, tidak disebarluaskan.
