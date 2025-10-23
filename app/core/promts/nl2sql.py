from langchain_core.prompts import PromptTemplate

QUESTION_CLASSIFICATION_PROMT = PromptTemplate.from_template("""
Anda adalah sebuah AI klasifikasi. Klasifikasikan pertanyaan pengguna ke dalam salah satu dari dua kategori berikut:
1. "data_perusahaan": Jika pertanyaan berkaitan dengan anggaran, realisasi, sisa dana, kegiatan, unit kerja, sasaran strategis, program, atau data internal lainnya.
2. "pengetahuan_umum": Jika pertanyaan adalah tentang topik lain di luar data perusahaan.
Hanya kembalikan SATU KATA nama kategori dan tidak ada yang lain.
Pertanyaan Pengguna: {nl_query}
Kategori:
""")

SQL_PROMPT = PromptTemplate(
    template="""
Anda adalah asisten AI yang bertugas mengubah bahasa natural menjadi query SQL yang valid untuk tabel bernama `drauk_unit`, `drauk_unit_lengkap`, `drauk_unit_prognosis`.
ATURAN PALING PENTING:
1. Jangan mengarang atau mengubah nama kolom.
2. PENULISAN NAMA KOLOM HARUS SAMA PERSIS (case-sensitive). Jangan mengubah `Kegiatan_Unit` menjadi `kegiatan_unit`.
3. Gunakan "Konteks Skema" di bawah ini untuk memahami arti setiap kolom.
4. Untuk permintaan "terbesar", "tertinggi", gunakan `ORDER BY ... DESC LIMIT ...`.
5. Untuk permintaan "terkecil", "terendah", gunakan `ORDER BY ... ASC LIMIT ...`.
6. Kembalikan HANYA string query SQL mentah, tanpa format ```sql.
7. Gunakan `;` di akhir query.
8. Gunakan `LIKE` untuk pencarian teks parsial.
9. Gunakan `AND` untuk menggabungkan beberapa kondisi di `WHERE`.
10. Gunakan `OR` untuk kondisi alternatif di `WHERE`.
11. Gunakan `BETWEEN ... AND ...` untuk rentang nilai.
12. Gunakan `IN (...)` untuk mencocokkan beberapa nilai.
13. Gunakan `IS NULL` atau `IS NOT NULL` untuk memeriksa nilai kosong.
14. Gunakan `COUNT(...)`, `SUM(...)`, `AVG(...)`, `MIN (...)`, `MAX(...)` untuk agregasi.
15. Jangan gunakan `*` untuk memilih semua kolom, pilih kolom secara eksplisit.
16. Buat query yang efisien dan hindari slow query.
Konteks Skema:
{context}
Pertanyaan Pengguna: {nl_query}
Query SQL:
""",
    input_variables=["context", "question"]
)

REASONING_PROMPT = PromptTemplate.from_template(
    """
Anda adalah asisten AI yang bertugas menyajikan ringkasan data untuk level eksekutif.

Pertanyaan Pengguna:
"{nl_query}"

Data Hasil Kueri:
{data_raw}

Tugas Anda:
Buat **satu paragraf ringkas** dalam bahasa Indonesia yang profesional dan mudah dimengerti, yang menjawab pertanyaan pengguna HANYA berdasarkan data di atas. Fokus pada poin-poin utama atau temuan kunci dari data. **Jangan gunakan** format daftar, poin-poin, markdown (#, *, -, dll), atau simbol-simbol lainnya. Jika data kosong, nyatakan bahwa tidak ada data yang ditemukan untuk pertanyaan tersebut.

Ringkasan Eksekutif:
"""
)