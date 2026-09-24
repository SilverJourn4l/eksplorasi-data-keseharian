# Protokol pelabelan stance judul berita (Edisi 004)

Disusun: 22 September 2026. Protokol ini mengunci cara satu judul berita
diklasifikasikan ke dalam stance terhadap pengerukan/ekspor pasir laut.

## Satuan analisis

Judul berita (bukan isi artikel), beserta nama media dan tanggal terbit,
dipanen dari agregator Google News. Judul dipilih karena singkat dan faktual;
isi artikel tidak disalin sehingga yang dikutip hanya teks pendek.

## Gerbang relevansi (lapisan pertama)

Google News mencocokkan kueri sampai ke isi artikel, sehingga sebagian judul
tidak menyinggung topik sama sekali. Judul dinyatakan RELEVAN hanya bila
memuat frasa inti: "pasir laut", "sedimentasi laut", "sedimen laut",
"sedimen di laut", "hasil sedimentasi", "ekspor pasir", "tambang pasir",
"penambangan pasir", "pengerukan pasir", "keruk pasir", "kapal isap",
"kapal keruk", "penyedot pasir", "curi pasir", "pencurian pasir",
"pasir ilegal", dengan pengecualian "pasir timah" dan "pasir besi".
Judul di luar itu disisihkan dan dilaporkan jumlahnya; analisis stance hanya
berjalan atas judul relevan.

## Label

| Label | Definisi operasional |
|---|---|
| `menolak` | Judul memuat penanda sikap menentang/mengkritik aktivitas atau kebijakannya (penolakan, kecaman, gugatan, peringatan dampak) |
| `mendukung` | Judul memuat penanda sikap membela/meyakini manfaat atau keamanan aktivitas/kebijakannya |
| `campuran` | Kedua penanda muncul sekaligus dalam satu judul |
| `netral` | Tidak ada penanda stance; judul melaporkan peristiwa, angka, atau proses |

Klasifikasi primer bersifat **deterministik** (leksikon kata kunci terbuka di
`label_stance.py`) supaya siapa pun bisa mereproduksi hasil yang sama persis.
Kualitas leksikon diuji lewat **audit acak** oleh penilai manusia/LLM yang
terpisah dari kode leksikon.

## Aturan keputusan

1. Gelar frasa judul dalam huruf kecil, ganti "ijin" dengan "izin", buang tanda
   baca selain huruf-spasi-angka.
2. Hitung penanda `menolak` dan `mendukung` yang cocok. Frasa multi-kata
   dicocokkan sebagai rangkaian utuh; kata dasar dicocokkan sebagai substring
   token sehingga afiks tetap tertangkap ("kerusakannya" tetap kena "rusak").
3. Pengecualian: istilah "kerugian negara" membatalkan sinyal kata "rugi"
   (konteks hukum), dan "sangat kecil" membatalkan sinyal manfaat/penerimaan.
4. Aturan tanya: judul bertanya tanpa penanda menolak tidak dihitung mendukung.
5. Stance dinilai terhadap AKTIVITAS pengerukan/ekspor pasir laut, bukan
   terhadap beritanya: laporan faktual kebijakan/putusan pengadilan = netral;
   pernyataan yang memuji/membela pelarangan ekspor = menolak; pembelaan
   terhadap pembukaan ekspor = mendukung.
6. Hanya menolak yang cocok -> `menolak`; hanya mendukung -> `mendukung`;
   keduanya ada -> `campuran`; tidak ada -> `netral`.

Catatan revisi: leksikon ini revisi pasca-audit ronde 1 (201 judul, kesepakatan
di bawah ambang 80 persen). Kesalahan sistemis ronde 1 yang diperbaiki: afiks
tak tertangkap, penanda hilang (stop, tunda, lawan, sorot, desak, jual negara,
greenwashing), false positive laporan penindakan dan laporan putusan, serta
frasa "cabut izin" tanpa kata desakan.

## Audit (penguncian seed)

- Seed acak: **42** (numpy default_rng).
- Sampel audit: 200 judul diambil acak berstrata proporsional per episode,
  dari gabungan seluruh label (termasuk `netral`).
- Penilai audit tidak memakai leksikon; menilai dari bunyi judul sesuai tabel
  definisi di atas. Hasil audit disimpan di `data/audit-labeling.csv`.
- Metrik yang dilaporkan: proporsi kesepakatan keseluruhan dan matriks
  kebingungan per label. Bila kesepakatan di bawah 80 persen, leksikon
  direvisi dan audit diulang.

## Keterbatasan yang diakui

- Judul adalah ringkasan redaksi, bukan suara warga langsung; angka stance
  menggambarkan **nada pemberitaan**, bukan hasil jajak pendapat.
- Google News mengurutkan hasil per jendela menurut relevansi; jendela yang
  menyentuh batas 100 item dibelah sampai level hari, jendela yang tetap
  menyentuh batas dilaporkan sebagai keterbatasan.
- Duplikasi antar-kueri dibuang berdasarkan judul bersih; berita dengan judul
  berbeda tapi isi sama tetap bisa terhitung ganda.
