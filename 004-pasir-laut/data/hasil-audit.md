# Hasil audit pelabelan stance (Edisi 004)

Audit sesuai `protokol-labeling.md`: sampel acak berstrata per episode,
seed 42, dinilai dari bunyi judul tanpa memakai leksikon.

## Ronde 1 (201 judul, korpus belum disaring relevansi)
- Temuan utama: sekitar 25 persen sampel tidak relevan dengan topik;
  kesepakatan stance di bawah ambang. Leksikon direvisi dan gerbang
  relevansi ditambahkan.

## Ronde 2 (199 judul, pasca-gerbang relevansi)
- Kesepakatan sekitar 80 persen; di bawah/sama ambang, revisi kedua
  dijalankan sesuai protokol. Perbaikan: penanda "nolak" (lebur nasal),
  false positive "pemanfaatan"/"sejarah", kata "rugi" dan "bahaya" yang
  hilang saat tulis ulang, penanda baru (haram, gerus, dihapus, pelanggaran
  HAM, sejarah peradilan, negara terlalu lemah), aturan konteks sidang,
  pengecualian "kerugian negara" dan "tidak haram".

## Ronde 3 verifikasi (199 judul)
- **Kesepakatan 185/199 = 93 persen** (di atas ambang 80 persen).
- Sisa 14 selisih, rincian arah:
  - 2 judulrelevansi sisa (perpustakaan, karya seni) lolos gerbang frasa;
  - 6 judul penolakan halus tak tertangkap ("seriuslah mencegah", "benarkah
    demi kesehatan laut?", "umurnya pendek", "pajak melebihi target",
    "ombudsman angkat bicara", "bantah ilegal klaim izin");
  - 4 judul abu-abu (disebut bertentangan UU, ilegal di banyak tempat,
    reklamasi PIK, putusan MA dipuji);
  - 2 lainnya selisih kategori borderline.
- Arah selisih mayoritas adalah LUPUT pada sinyal lemah, sehingga proporsi
  "menolak" yang dilaporkan berpotensi sedikit TERLALU RENDAH, bukan
  digelembungkan.

## Catatan keterbatasan auditor
Audit dilakukan satu penilai (asisten AI jurnal) tanpa penilai kedua
independen; angka kesepakatan adalah batas atas keandalan. Leksikon dan
protokol dipublikasikan penuh agar auditor lain dapat mengulang.
