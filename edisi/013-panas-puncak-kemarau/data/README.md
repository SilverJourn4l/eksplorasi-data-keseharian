# Data edisi 013: panas puncak kemarau, dibandingkan dengan Edisi 001

## Sumber (kontrak identik dengan Edisi 001)

- **Open-Meteo Historical Weather API (reanalisis ERA5)**, titik grid
  -6,18 / 106,83 (Jakarta Pusat), suhu harian maksimum, minimum, dan
  rata-rata, 1950-01-01 sampai tanggal panen 2026-10-01 (28.033 hari).
  Mentah apa adanya di `mentah/open-meteo-era5-jakarta.json`.
- **NASA POWER (MERRA-2)**, titik sama, diunduh per tahun sejak 1984
  (memangkas tiga hari terakhir September 2026 pada tanggal panen; dicatat
  di metrik). Mentah di `mentah/nasa-power-jakarta.json`.
- Catatan kelayakan BMKG dari Edisi 001 (API historis memerlukan akun dan
  kunci) dibaca ulang dan tidak berubah statusnya.

## Perbedaan dari Hash Edisi 001 (yang memang berubah)

1. Panen menjangkau 1 Oktober 2026, sehingga edisi ini menambahkan **musim
   kemarau 2026 penuh** (92 hari, 1 Juli sampai 30 September 2026).
2. Ukuran **1950-2025 tidak diubah definisinya** dan dicocokkan kembali ke
   limabelas patokan Edisi 001 pada presisi tampilannya; replikasinya
   bersih (lihat `metrik-013.json`, kunci `replikasi_001`).
3. Skrip menulis `tanggal-panen.txt` supaya klaim "diakses tanggal berapa"
   di README dan grafik selalu konsisten.

## Berkas

- `suhu-harian-jakarta.csv`: 28.033 baris, kolom tanggal, tmax/tmin/tmean
  ERA5, dan kolom pembanding NASA POWER (kosong untuk hari yang belum
  diterbitkan produknya).
- `tanggal-panen.txt`, `metrik-013.json` (ditulis notebook).

Lisensi data: layanan publik iklim dikutip untuk analisis dengan atribusi;
berkas mentah disimpan lokal untuk reproducibility.
