from langchain_core.language_models import BaseLanguageModel
from .gemini_adapter import get_gemini_llm
from .openrouter_adapter import get_openrouter_llm

def get_llm_adapter(model_name: str) -> BaseLanguageModel:
    """
    Factory function yang memilih dan mengembalikan adapter LLM yang sesuai
    berdasarkan nama model.
    """
    model_lower = model_name.lower()

    if "gemini" in model_lower:
        print(f"✅ Routing to Gemini for model: {model_name}")
        return get_gemini_llm(model_name)
    else:
        # Default ke OpenRouter untuk semua model lainnya
        print(f"✅ Routing to OpenRouter for model: {model_name}")
        return get_openrouter_llm(model_name)