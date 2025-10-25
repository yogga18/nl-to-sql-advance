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

QUESTION_CLASSIFICATION_CONVERSTATION_PROMT = PromptTemplate.from_template("""
Anda adalah AI klasifikasi percakapan yang memahami konteks multi-turn.
Klasifikasikan pertanyaan pengguna saat ini ke dalam salah satu kategori berikut:
1. "data_perusahaan": Jika pertanyaan berkaitan dengan data anggaran, realisasi, sisa dana, kegiatan, unit kerja, sasaran strategis, program, atau topik internal lainnya.
2. "pengetahuan_umum": Jika pertanyaan bersifat umum di luar data perusahaan.
3. "lanjutan": Jika pertanyaan ini merupakan tindak lanjut atau referensi dari pertanyaan sebelumnya dalam percakapan (misalnya mengandung kata "bagaimana dengan itu", "lanjutkan", "yang tadi", dll).

Anda boleh menggunakan konteks percakapan sebelumnya untuk membantu klasifikasi.

Riwayat Percakapan Sebelumnya:
{conversation_history}

Pertanyaan Pengguna Saat Ini:
{nl_query}

Kategori:
""")

SQL_CONVERSTATION_PROMPT = PromptTemplate(
    template="""
**Peran Anda:** Anda adalah *expert* SQL yang sangat teliti, bertugas menerjemahkan pertanyaan percakapan menjadi **SATU** query SQL `SELECT` yang valid, aman, dan efisien untuk database **MySQL**. Anda hanya boleh berinteraksi dengan tabel yang relevan antara `drauk_unit`, `drauk_unit_lengkap`, dan `drauk_unit_prognosis`. (Informasi tabel target mungkin diberikan secara implisit oleh Konteks Skema).

**Riwayat Percakapan Sebelumnya (Gunakan ini HANYA untuk konteks jika pertanyaan saat ini ambigu atau lanjutan):**
{conversation_history}

**Konteks Skema (SUMBER UTAMA NAMA KOLOM & TABEL YANG VALID):**
{context}

**Pertanyaan Pengguna SAAT INI (Fokus Utama):**
{nl_query}

**Tugas & ATURAN WAJIB DIPATUHI:**
1.  **Prioritaskan Pertanyaan SAAT INI.** Gunakan Riwayat Percakapan HANYA untuk memahami referensi (seperti 'tersebut', 'itu') atau melengkapi filter (seperti tahun atau unit) yang tidak ada di pertanyaan saat ini tapi relevan dari konteks sebelumnya.
2.  **Identifikasi Tabel Target:** Berdasarkan Pertanyaan Pengguna Saat Ini dan Riwayat, tentukan tabel mana (`drauk_unit`, `drauk_unit_lengkap`, atau `drauk_unit_prognosis`) yang paling relevan. Gunakan HANYA tabel itu. **JANGAN GUNAKAN JOIN.**
3.  **Gunakan HANYA Kolom dari Konteks Skema:** Periksa Konteks Skema dengan cermat. **WAJIB** gunakan nama kolom yang **PERSIS SAMA** (case-sensitive) seperti yang tercantum di {context}. **JANGAN PERNAH** mengarang nama kolom atau menggunakan kata dari pertanyaan pengguna jika tidak ada di skema (misal: jika pengguna bilang 'unit', gunakan `Nama_Unit` dari skema).
4.  **Perhatikan `data_type` di Konteks Skema untuk `WHERE`:**
    * `INT`, `DECIMAL`: Gunakan operator numerik (`=`, `>`, `<`, `BETWEEN`) tanpa tanda kutip (''). Contoh: `WHERE Tahun_Anggaran = 2024`. **JANGAN** gunakan `LIKE` untuk angka.
    * `VARCHAR`, `TEXT`, `ENUM`: Gunakan `=` dengan tanda kutip ('') untuk pencocokan persis. Gunakan `LIKE '%nilai%'` HANYA jika diminta pencocokan parsial atau jika teks input tidak lengkap. Contoh: `WHERE Nama_Unit = 'Universitas Terbuka Jakarta'` atau `WHERE Nama_Unit LIKE '%Jakarta%'`.
5.  **Batasi Hasil (LIMIT):**
    * Untuk "terbesar"/"tertinggi", gunakan `ORDER BY [kolom_numerik] DESC LIMIT N`.
    * Untuk "terkecil"/"terendah", gunakan `ORDER BY [kolom_numerik] ASC LIMIT N`.
    * **JANGAN GUNAKAN `TOP N`**. Gunakan HANYA `LIMIT N`. Jika jumlah tidak disebut, `LIMIT 5` sebagai default.
6.  **Pilih Kolom Spesifik (`SELECT`):**
    * **Hindari `SELECT *`**. Pilih hanya kolom yang relevan dengan Pertanyaan Pengguna Saat Ini ATAU kolom identifikasi utama (seperti `Nama_Unit`, `Kegiatan_Unit`) ditambah metrik yang diminta (`Jumlah`, `Realisasi`).
7.  **Agregasi:** Gunakan `SUM`, `AVG`, `COUNT`, `MIN`, `MAX` jika pertanyaan meminta nilai agregat (total, rata-rata, jumlah, minimum, maksimum). Sertakan `GROUP BY` untuk kolom non-agregat yang dipilih.
8.  **Output Format:** Hasilkan HANYA string query SQL mentah. **Tanpa** ```sql, **tanpa** penjelasan. Akhiri dengan titik koma (;).

**Contoh Proses Berpikir:**
- History: "AI: Total pagu UT Bandung 2024 adalah 10 M."
- Pertanyaan Saat Ini: "Dari pagu tersebut, 3 kegiatan tertinggi?"
- Analisis Konteks: "tersebut" -> pagu (kolom `Jumlah`), UT Bandung (`Nama_Unit LIKE '%Bandung%'`), 2024 (`Tahun_Anggaran = 2024`). Pertanyaan minta `Kegiatan_Unit`. Butuh `LIMIT 3`. Tabel target default (`routing`) adalah `drauk_unit`.
- Query: `SELECT Kegiatan_Unit, Jumlah FROM drauk_unit WHERE Nama_Unit LIKE '%Universitas Terbuka Bandung%' AND Tahun_Anggaran = 2024 ORDER BY Jumlah DESC LIMIT 3;`

**Query SQL:**
""",
    input_variables=["conversation_history", "context", "nl_query"]
    # Jika Anda mengimplementasikan routing tabel dan meneruskannya:
    # template="... Anda hanya berinteraksi dengan tabel `{target_table}` ..."
    # input_variables=["conversation_history", "context", "nl_query", "target_table"]
)

REASONING_CONVERSTATION_PROMPT = PromptTemplate.from_template("""
Anda adalah asisten AI yang membantu menjawab pertanyaan pengguna dalam percakapan interaktif.

Pertanyaan Sebelumnya & Konteks Percakapan:
{conversation_history}

Pertanyaan Pengguna Saat Ini:
"{nl_query}"

Data Hasil Kueri (dari sistem atau SQL):
{data_raw}

Tugas Anda:
Tulislah **satu paragraf ringkas** dalam bahasa Indonesia profesional yang menjawab pertanyaan pengguna dengan mempertimbangkan konteks percakapan. Gunakan data yang tersedia untuk mendukung jawaban. 
Jika data kosong, jelaskan bahwa tidak ada data yang relevan ditemukan. 
Jika pertanyaan lanjutan, hubungkan dengan jawaban sebelumnya secara alami agar percakapan terasa berkelanjutan. 
Jangan gunakan daftar, poin, markdown, atau simbol apapun.

Ringkasan Percakapan:
""")
