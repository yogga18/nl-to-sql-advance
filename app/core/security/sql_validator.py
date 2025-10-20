import sqlparse
from sqlparse.sql import Identifier
from sqlparse.tokens import Keyword, DML
import re

BLACKLISTED_FUNCTIONS = {
    'SLEEP',
    'BENCHMARK',
    'LOAD_FILE',
    'SYS_EVAL',
    'SYS_EXEC',
    'SYS_GET', 
    'EXECUTE',
}

BLACKLISTED_KEYWORDS = {
    'INTO',
    'FOR',
    'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'REPLACE', 'TRUNCATE',
    'GRANT', 'REVOKE',
    'LOCK', 'UNLOCK',
    'EXECUTE',
}

def sanitize_sql_output(sql_string: str) -> str:
    """Membersihkan output LLM dari format Markdown code block."""
    match = re.search(r"```sql\n(.*?)\n```", sql_string, re.DOTALL)
    if match:
        return match.group(1).strip()
    return sql_string.strip()

def is_safe_select_query(query: str) -> bool:
    """
    Memvalidasi sebuah string query SQL untuk memastikan itu adalah
    query SELECT tunggal yang aman dan tidak mengandung fungsi/klausa berbahaya.
    """
    parsed = sqlparse.parse(query)
    if not parsed or len(parsed) == 0:
        return False

    if len(parsed) > 1:
        print("Validasi Gagal: Terdeteksi lebih dari satu statement SQL.")
        return False
        
    statement = parsed[0]
    
    if statement.get_type() != 'SELECT':
        print(f"Validasi Gagal: Tipe statement bukan SELECT, melainkan {statement.get_type()}.")
        return False
        
    for token in statement.flatten():
        if token.ttype is Keyword and token.normalized in BLACKLISTED_KEYWORDS:
            print(f"Validasi Gagal: Terdeteksi kata kunci berbahaya '{token.normalized}'.")
            return False

        if isinstance(token, Identifier):
            is_function_call = any(isinstance(sub_token, sqlparse.sql.Parenthesis) for sub_token in token.tokens)
            if is_function_call:
                function_name = token.get_name()
                if function_name and function_name.upper() in BLACKLISTED_FUNCTIONS:
                    print(f"Validasi Gagal: Terdeteksi pemanggilan fungsi berbahaya '{function_name.upper()}'.")
                    return False
    
    print("Validasi query SELECT berhasil.")
    return True
