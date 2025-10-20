# Service Chatbot (RAG Service)

Proyek ini adalah contoh service RAG (Retrieval-Augmented Generation) dengan arsitektur terpisah (adapters, core, services). Aplikasi dibangun menggunakan FastAPI dan beberapa adapter LangChain untuk LLM, embedding, dan vektor-store (Qdrant).

README ini berbahasa Indonesia dan berisi langkah cepat untuk setup, environment variables, cara menjalankan, dan catatan pengembangan.

## Fitur utama

- Endpoints FastAPI untuk chat dan NL-to-SQL
- Integrasi dengan Qdrant sebagai vector store
- Adapter untuk menggunakan SentenceTransformers / HuggingFace embeddings
- Patern clean-architecture (adapters, core, services)

## Prasyarat

- Python 3.10+ (direkomendasikan 3.11)
- PostgreSQL / MySQL jika kamu ingin menyambungkan database untuk contoh SQL (sesuaikan `adapters/db`)
- Qdrant (remote atau lokal) jika ingin menggunakan vector store

## Setup cepat (lokal)

1. Clone repo dan masuk ke folder:

```bash
cd /path/to/service_chatbot
```

2. Buat virtual environment dan aktifkan (zsh):

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependency:

```bash
pip install -r requirements.txt
```

4. Buat file `.env` di root (contoh nilai minimal):

```env
QDRANT_HOST=localhost
QDRANT_API_KEY=
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
LLM_MODEL_NAME=gemini-2.5-flash
COLLECTION_NAME=my_documents
GEMINI_MODEL_NAME=gemini-pro
# Tambahkan credential LLM (OPENAI_API_KEY, OPENROUTER_API_KEY, dsb.) jika diperlukan
```

5. Jalankan aplikasi:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Buka http://127.0.0.1:8000/docs untuk melihat Swagger/OpenAPI.

## Environment variables yang sering dipakai

- `QDRANT_HOST` — host Qdrant
- `QDRANT_API_KEY` — API key Qdrant (opsional)
- `EMBEDDING_MODEL_NAME` — nama model embedding (mis. `all-mpnet-base-v2`)
- `LLM_MODEL_NAME` — model default LLM
- `COLLECTION_NAME` — nama koleksi Qdrant
- `GEMINI_MODEL_NAME` — contoh nama model Gemini
- `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, dsb. — credential untuk provider LLM

## Struktur proyek (ringkas)

- `app/`
  - `adapters/` — penghubung ke layanan eksternal (API, embeddings, llm, vector stores)
  - `core/` — utilitas domain, mis. sanitasi SQL, eksekusi DB
  - `services/` — logika bisnis (NL2SQL, RAG, dsb.)
  - `config.py` — konfigurasi yang membaca env vars
- `main.py` — entrypoint FastAPI
- `requirements.txt` — dependensi pip

## Catatan pengembangan

- Jika Pylance/VSCode menandai import `config` sebagai unknown, pastikan root proyek adalah folder yang memuat `main.py` dan `app/` di PYTHONPATH. Alternatif yang lebih baik: gunakan `from app import config` atau buat `settings = Settings()` menggunakan Pydantic di `app/config.py` untuk autocompletion.

- Untuk menggunakan local Qdrant: jalankan `qdrant` container atau paket biner Qdrant lokal dan set `QDRANT_HOST`.

- Jika kamu ingin fitur "fast return" (hanya kembalikan data mentah tanpa reasoning), pertimbangkan menambahkan parameter `with_reasoning: bool = True` pada `NL2SQLService.execute_flow`.

## Tes & Debugging cepat

- Lakukan panggilan ke endpoint `/api/v1/nl2sql` dari Swagger UI atau `curl` untuk menguji alur.
- Tambahkan logging atau print statements sementara jika butuh tracing di LLM calls.

## Kontribusi

Silakan ajukan PR untuk perbaikan, dokumentasi, atau fitur baru. Ikuti konvensi commit yang konsisten.

---

Jika mau, saya bisa:

- Tambahkan badge status, license, atau CONTRIBUTING.md
- Buatkan contoh `.env.example` dan skrip makefile untuk pengembangan
- Menambahkan instruksi deploy Docker

Beritahu bagian mana yang ingin kamu perkuat selanjutnya.
