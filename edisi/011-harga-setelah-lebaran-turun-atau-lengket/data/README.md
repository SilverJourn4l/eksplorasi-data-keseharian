# Data edisi 011: harga pasca-Lebaran, turun atau lengket

## Sumber

Tanpa panggilan jaringan. Edisi ini menyusun pengukuran barunya murni dari
panen PIHPS Edisi 008 yang tersimpan di `edisi/008/data/`:

- `edisi/008/data/harga-nasional-mingguan.csv` — rerata nasional mingguan
  (snapshot Rabu) sepuluh komoditas, 2019-03-13 s.d. 2026-04-29, pasar
  tradisional PIHPS (bi.go.id/hargapangan), diunduh Edisi 008.
- `edisi/008/data/tanggal-ramadan.csv` — tanggal 1 Ramadan dan Idulfitri
  1440-1447 H berdasarkan pengetapan pemerintah, disalin ke direktori ini.

## Metodologi perhitungan (dirumuskan di unduh_data.py)

- basis(k, H): rerata minggu -70 s.d. -35 relatif 1 Ramadan musim H.
- kenaikan puncak: maksimum harga/basis jendela -35 s.d. +8 relatif Lebaran;
  musim diuji bila kenaikan >= 2%.
- sisa: harga/basis snapshot Rabu terdekat ke +30/+42 hari (toleransi 4 hari).
- indeks lengket: (sisa-1)/(puncak-1).

## Hasil dan kekosongan data yang diakui

70 baris diproduksi (10 komoditas x 7 musim). Musim 1442 H gugur serentak
karena celah rilis sumber membuat jendela Ramadan berjumlah di bawah enam
snapshot (dokumentasinya di `edisi/008/data/README.md`). Dari 70 baris, 51
lolos ambang pengujian (naik >= 2%); sebagian kecil memiliki sisa +30 atau +42
kosong (snapshot musiman berikutnya belum atau sudah tidak tersedia) dan
dijatuhkan dari ukuran yang relevan melalui `dropna`, bukan diisi.

## Berkas

- `harga-lengket.csv`: 70 baris pasangan komoditas x musim dengan semua
  kolom definisi dan bendera `diuji`.
- `tanggal-ramadan.csv`: salinan kalender resmi (identik dengan Edisi 008).
- `metrik-011.json`: dicetak notebook; median lengket + selang 95%
  (bootstrap 10.000 ulang, benih 2026) per komoditas.

Lisensi data: dikutip dari sumber terbuka untuk analisis dengan atribusi.
