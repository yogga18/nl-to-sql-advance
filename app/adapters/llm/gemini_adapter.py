from langchain_google_genai import ChatGoogleGenerativeAI

def get_gemini_llm(model_name: str):
    """Mengembalikan instance LLM Gemini yang siap pakai."""
    return ChatGoogleGenerativeAI(
        model=model_name, 
        temperature=0,
    )