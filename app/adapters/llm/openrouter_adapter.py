from langchain_openai import ChatOpenAI
from app import config
from pydantic import SecretStr

def get_openrouter_llm(model_name: str):
    """
    Mengembalikan instance LLM yang terhubung ke OpenRouter
    menggunakan adapter ChatOpenAI yang universal.
    """
    return ChatOpenAI(
        model=model_name,
        temperature=0.1,
        base_url="https://openrouter.ai/api/v1",
        api_key=SecretStr(config.OPENROUTER_API_KEY),
        
        default_headers={
            "HTTP-Referer": "<YOUR_SITE_URL>", 
            "X-Title": "<YOUR_SITE_NAME>",
        }
    )