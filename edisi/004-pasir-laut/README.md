# Pengerukan pasir laut: suara publik dan aturan berpihak ke mana?

Indonesia punya hubungan aneh dengan pasir lautnya sendiri. Tahun 2003 ekspor
pasir laut dilarang karena pulau-pulau kecil mulai tenggelam. Dua dekade
kemudian, Mei 2023, larangan itu dibuka lagi lewat PP 26/2023 dengan judul
halus "pengelolaan hasil sedimentasi". September 2024 keran ekspornya resmi
mengalir. Lalu Juni 2025 Mahkamah Agung membatalkannya. Saya penasaran: di
tengah ayunan aturan itu, suara siapa yang paling sering muncul di berita, dan
nada pemberitaan condong ke mana?

## Datanya dari mana

Saya memanen judul berita dari agregator Google News: lima frasa kunci
("pasir laut", "ekspor pasir laut", "sedimentasi laut", "penambangan pasir
laut", "pengerukan pasir laut"), Januari 2022 sampai September 2026, jendela
bulanan yang dibelah sampai harian bila menyentuh batas 100 item. Hasilnya
1.371 judul dari 246 media. Karena Google News mencocokkan sampai ke isi
artikel, sepertiganya ternyata tidak membahas topik ini sama sekali (ada
berita voli, ada seniman menyulam pasir). Gerbang relevansi menyisakan 735
judul yang benar-benar bicara pasir laut, masing-masing dilabeli nadanya:
menolak, mendukung, netral, atau campuran, memakai leksikon terbuka yang
diaudit acak dengan kesepakatan 93 persen. Satuan analisisnya judul, bukan isi
artikel, jadi yang diukur adalah nada pemberitaan, bukan hasil jajak pendapat.

## Bandul aturannya

Cerita ini saya bagi lima babak, mengikuti ayunan regulasi:

1. **Sebelum PP** (Jan 2022 - Mei 2023). Ekspor masih dilarang; berita
   didominasi penambangan ilegal dan kasus korupsi pasir Takalar.
2. **PP disahkan** (Mei - Des 2023). PP 26/2023 diteken 15 Mei 2023 dan
   membuka lagi pemanfaatan pasir laut, termasuk ekspor bila kebutuhan dalam
   negeri terpenuhi. Banjir kritik dari WALHI, Greenpeace, sampai DPR.
3. **Aturan persiapan** (Jan - Agu 2024). Harga patokan dan spesifikasi pasir
   ekspor disusun (Kepmen KP 6 dan 47/2024). Pemberitaan sepi.
4. **Ekspor dibuka** (Agu 2024 - Jun 2025). Permendag 20 dan 21/2024
   diundangkan 29 Agustus 2024; setelah 20 tahun, ekspor jalan lagi.
5. **Pasca putusan MA** (Jun 2025 - Sep 2026). Putusan MA 5/P/HUM/2025 pada
   2 Juni 2025 menyatakan pasal ekspornya bertentangan dengan UU Kelautan;
   Permen KKP 6/2026 mengukuhkan pasir laut hanya untuk kebutuhan dalam negeri.

## Apa kata angkanya

Pola yang muncul sederhana dan konsisten. Di kelima babak, judul bernada
menolak selalu jauh lebih banyak daripada judul mendukung: 26,5 persen
(pra-PP), 32,0 persen (PP disahkan), 15,3 persen (babak jeda), 32,3 persen
(ekspor dibuka), dan 35,6 persen (pasca putusan MA). Judul mendukung tidak
pernah lewat 3,4 persen di babak mana pun. Sisi pendukung hampir tidak
terdengar.

Supaya tidak tertebak fluktuasi sampel kecil, tiap proporsi saya beri interval
kepercayaan Wilson, dan selisih antar-babak diuji dengan metode Newcombe.
Alat pikirnya begini: proporsi adalah tebakan terbaik, interval adalah rentang
yang masuk akal untuk nilai sejatinya, dan kalau interval selisih dua babak
tidak menyentuh nol, bedanya sulit dianggap kebetulan. Hasilnya: dibanding
babak jeda yang sepi, proporsi penolakan naik 16,8 poin saat PP disahkan, 17,0
poin saat ekspor dibuka, dan 20,3 poin pasca putusan MA. Ketiganya signifikan.
Volume beritanya pun bereaksi: puncak pemberitaan terjadi Juni 2023 (159 judul
sebulan), tepat setelah PP diteken, lalu melonjak lagi September 2024 saat
keran ekspor dibuka.

## Batasnya, jujur

Tiga hal perlu dibilang. Pertama, judul berita adalah ringkasan redaksi, bukan
suara warga langsung; angka ini menggambarkan apa yang disuarakan media, dan
media bukan pengganti jajak pendapat. Kedua, pembanding pra-PP hanya 34 judul,
jadi kenaikan dari E0 ke E1 tidak bisa diklaim signifikan; klaim kenaikan
dipatok pada kontras terhadap babak jeda. Ketiga, arah keliru leksikon yang
tersisa dari audit cenderung luput menangkap sinyal halus, sehingga proporsi
menolak yang dilaporkan berpotensi sedikit terlalu rendah, bukan digelembungkan.

Dan satu hal yang menarik dari audit: judul yang merayakan pelarangan ekspor
oleh MA tetap dihitung sebagai suara menolak ekspor, sesuai protokol. Itulah
sebabnya babak pasca putusan MA justru mencatat proporsi menolak tertinggi.

## Cara reproduksi

```bash
python3 tools/data_scraping.py     # panen judul dari Google News RSS (butuh internet)
python3 label_stance.py   # gerbang relevansi + leksikon stance
python3 -m nbconvert --to notebook --execute --inplace analisis.ipynb
```

Semua berkas pendukung terbuka: `data/protokol-labeling.md` (aturan label dan
audit), `data/hasil-audit.md` (hasil tiga ronde audit), `label_stance.py`
(leksikon lengkap), dan `data/linimasa-regulasi.csv` (linimasa aturan dengan
rujukan). Panen diulang pada 22 September 2026.
