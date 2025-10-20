import yaml
from pathlib import Path
from dotenv import load_dotenv
import os
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant

# === Load env dan konfigurasi dasar ===
load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
QDRANT_COLLECTION = os.getenv("COLLECTION_NAME", "schema_docs")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL_NAME", "all-mpnet-base-v2")
print(f"🔧 Menggunakan Qdrant host: {QDRANT_HOST}")
print(f"🔧 Menggunakan koleksi Qdrant: {QDRANT_COLLECTION}")
print(f"🔧 Menggunakan model embedding: {EMBED_MODEL}")

# Lokasi file YAML
BASE_PATH = Path(__file__).resolve().parent.parent / "data"
YAML_FILES = [
    BASE_PATH / "drauk_unit_schema.yml",
    BASE_PATH / "drauk_unit_lengkap_schema.yml",
    BASE_PATH / "drauk_unit_prognosis_schema.yml",
    BASE_PATH / "main_schema.yml",
]

# === Fungsi pembantu ===
def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def create_documents_from_table_yaml(table_name: str, data: dict, source_file: str):
    """Membuat Document LangChain dari schema YAML tabel."""
    docs = []
    table_info = data.get("spec", {}).get(table_name, {})
    if not table_info:
        return docs

    # Informasi kolom
    for column in table_info.get("columns", []):
        content = (
            f"Tabel '{table_name}' memiliki kolom '{column['name']}'. "
            f"Deskripsi: {column.get('description', 'Tidak ada deskripsi')}. "
            f"Tipe data: {column.get('data_type', 'Unknown')}. "
            f"Sinonim: {', '.join(column.get('synonyms', [])) if column.get('synonyms') else 'Tidak ada'}."
        )
        doc = Document(
            page_content=content,
            metadata={
                "source_file": source_file,
                "table": table_name,
                "column": column["name"],
                "data_type": column.get("data_type"),
                "synonyms": column.get("synonyms", []),
                "category": "column_definition",
            },
        )
        docs.append(doc)

    # Informasi umum tabel
    if table_info.get("description"):
        docs.append(
            Document(
                page_content=(
                    f"Tabel '{table_name}' berfungsi sebagai: {table_info['description']}. "
                    f"Aturan bisnis: {', '.join(table_info.get('business_rules', [])) if table_info.get('business_rules') else 'Tidak ada aturan bisnis'}."
                ),
                metadata={
                    "source_file": source_file,
                    "table": table_name,
                    "category": "table_description",
                },
            )
        )
    return docs

def create_documents_from_main_schema(data: dict, source_file: str):
    """Membuat Document dari file main_schema.yml."""
    docs = []
    for tbl in data.get("tables", []):
        content = (
            f"Tabel '{tbl['name']}' dijelaskan sebagai '{tbl.get('description', '')}'. "
            f"File schema: {tbl.get('file', '')}. "
            f"Key fields: {', '.join(tbl.get('key_fields', []))}. "
            f"Tipe data tabel: {tbl.get('type', 'Unknown')}. "
            f"Skor penting: {tbl.get('importance_score', 0)}."
        )
        docs.append(
            Document(
                page_content=content,
                metadata={
                    "source_file": source_file,
                    "table": tbl["name"],
                    "category": "table_summary",
                },
            )
        )
    return docs

# === Main ingest process ===
def main():
    all_docs = []

    for path in YAML_FILES:
        data = load_yaml(path)

        if "spec" in data:  # file schema tabel
            for tbl_name in data["spec"].keys():
                all_docs.extend(create_documents_from_table_yaml(tbl_name, data, path.name))

        elif "tables" in data:  # main_schema.yml
            all_docs.extend(create_documents_from_main_schema(data, path.name))

    print(f"✅ Total dokumen yang akan di-embed: {len(all_docs)}")

    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    print("🚀 Melakukan ingest ke Qdrant...")
    Qdrant.from_documents(
        all_docs,
        embeddings,
        url=QDRANT_HOST,
        api_key=QDRANT_API_KEY,
        collection_name=QDRANT_COLLECTION,
        prefer_grpc=False,  # aktifkan gRPC untuk performa tinggi
        force_recreate=True # true untuk menghapus koleksi lama dan buat baru, false untuk menambah ke koleksi yang ada
    )

    print("🎉 Ingest selesai! Semua schema berhasil disimpan ke Qdrant.")

if __name__ == "__main__":
    main()
