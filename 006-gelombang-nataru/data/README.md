# Data Edisi 006: gelombang Nataru, aksi dan niat

Dua sumber terbuka dengan peran berbeda: satu mencatat orang yang benar-benar pergi, satu mencatat orang yang mencari tiket.

## A. Perjalanan nyata: Kementerian Perhubungan (Posko Nataru 2024/25)

- Katalog: HUBNET Kemenhub, "Data Harian Pergerakan Penumpang Angkutan Lebaran, Natal dan Tahun Baru" (identifier `pergerakan-penumpang-event-kemenpar`),   diterbitkan Pusat Data dan Teknologi Informasi, dimutakhirkan 2 Desember 2025.
- Endpoint: `hubnet.kemenhub.go.id/dataset/get-data-api/microstrategy/data_event_kemenpar?event=NATARU%202024%202025&format=json`
- Isi: 105 baris = 5 moda x 21 hari (H-10 s.d. H+10, 15 Des 2024 - 4 Jan 2025):
  Angkutan Jalan, Angkutan Perkeretaapian, Angkutan Udara, Angkutan Laut, dan Angkutan SDP (sungai, danau, penyeberangan).
- Tanggal akses panen: 24 September 2026. Berkas: `pergerakan-nataru-2024-25.csv`, mentah di `mentah/trends/kemenhub-nataru-2024-2025.json`.
- Catatan penerbit: pantauan dilakukan H-7 s.d. H+10; data di luar periode itu **belum direkonsiliasi**. Angka rekap resmi yang beredar di berita (misalnya 17,18 juta penumpang angkutan umum) memakai definisi tersendiri; jumlah dari tabel terbuka ini berbeda sedikit (18,3 juta penumpang-hari seluruh moda) dan tulisan menyebut apa adanya sumber tabel.

## B. Niat mencari tiket: Google Trends

- Diambil lewat pustaka tak resmi `pytrends` ke trends.google.com, frasa:
  `tiket kereta api`, `tiket pesawat`, `tiket bus`, wilayah Indonesia (geo=ID), zona WIB, data harian per musim Nataru (Sep-Mar 2019/20 s.d. 2025/26), satu permintaan per musim. Berkas: `mentah/trends/trends-harian-2019.csv` s.d. `...-2025.csv`.
- Hal yang digarisbawahi:
  1. **Indeks relatif.** Angka adalah proporsi pencarian 0-100, bukan jumlah orang; setiap musim dinormalkan sendiri oleh server, maka lintas musim hanya dibaca sebagai lipatan terhadap dasar musim itu sendiri.
  2. **API tak resmi.** Google membatasi laju permintaan; panen awal tiga kali ditolak (HTTP 429) sebelum berhasil dengan jeda puluhan detik. Cache disimpan supaya tak perlu diulang.
  3. **Pencarian bukan perjalanan.** Frasa-frasa ini penanda niat; orang bisa mencari tanpa pergi (dan sebaliknya). Karena itu dua sumber dibiarkan bercerita berdampingan, tidak digabung jadi satu angka.
  4. Rentang multi-tahun coba diambil sekali jalan, tetapi server menurunkan resolusi menjadi bulanan pada rentang panjang; karena itu panen dipakai pola per-musim harian.
