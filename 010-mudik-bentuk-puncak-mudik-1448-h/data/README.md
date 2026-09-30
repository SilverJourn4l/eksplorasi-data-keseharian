# Data edisi 010: Mudik 1448 H: bentuk puncaknya

## Sumber utama (satu-satunya yang dibaca mesin)

Katalog HUBNET Kementerian Perhubungan, dataset "Data Harian Pergerakan
Penumpang Angkutan Lebaran, Natal dan Tahun Baru" (penerbit: Pusat Data dan
Teknologi Informasi Kemenhub):

- Endpoint: https://hubnet.kemenhub.go.id/dataset/get-data-api/microstrategy/data_event_kemenpar?format=json
- Diakses 30 September 2026; berkas mentah: `mentah/hubnet/data_event_kemenpar.json` (35,9 KB).
- Isi katalog saat diakses: tiga event, **ANGLEB 2024** dan **ANGLEB 2025**
  (mudik Idulfitri 1445 H dan 1446 H; masing-masing 22 hari, H-10 s.d. H+11)
  serta NATARU 2024 2025 (21 hari, dipakai hanya sebagai pembanding bayangan).
  Lima moda: Jalan, Perkeretaapian, Udara, Laut, SDP (sungai, danau,
  penyeberangan).
- Kolom periode khas katalog: `H 1`/`H 2` = hari Lebaran pertama/kedua;
  `H - k` = k hari sebelum Lebaran; `H + k` = k hari sesudahnya. Dipetakan ke
  `hari_relatif`: H 1 -> 0, H 2 -> 1, H + k -> 1+k, H - k -> -k.

## Batas melekat yang jujur

- Tabel adalah penumpang **angkutan umum** di simpul-simpul transportasi yang
  dipantau posko; kendaraan pribadi tidak terhitung (untuk itu katalog
  terpisah, di luar jangkauan edisi ini).
- Angka harian di luar jendela pantauan ditandai penerbit sebagai "belum
  direkonsiliasi"; edisi ini memakai apa adanya dan menuliskannya di batas
  tulisan.
- Katalog belum memiliki ANGLEB 2026 (mudik 1447 H, Maret 2026). Sisi tahun
  itu hanya muncul di "kerangka musim" sebagai realisasi rilis posko, bukan
  sebagai seri harian yang dianalisis.

## Sumber pendukung (dikutip naratif, tidak di parsing)

Rilis/siaran pers Posko Angkutan Lebaran Terpadu Kemenhub 2026 (kumulatif
H-8 s.d. H: 10.887.584 penumpang angkutan umum, +8,58% thdp 2025) dan realisasi
Mobile Positioning Data (147,55 juta pergerakan selama 17 hari), bersumber dari
dephub.go.id dan rekapan Tempo Data 31 Maret 2026. Survei potensi BKT:
146,48 juta (proyeksi 2025) vs realisasi 154,6 juta; 143,91 juta (proyeksi
2026) vs realisasi 147,55 juta.

## CSV

- `pergerakan-event.csv`: 325 baris (3 event x 5 moda x 21-22 hari), sumber
  kerja notebook.
- `metrik-010.json`: dicetak notebook: puncak per event/moda, bagian tiap
  sisi H, asimetri.

Lisensi data: dikutip dari katalog terbuka Kemenhub untuk kepentingan analisis
dengan atribusi.
