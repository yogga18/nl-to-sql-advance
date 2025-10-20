from typing import Dict, List, Any
from langchain_core.documents import Document

# 1. Definisikan build_prompt di sini, di tempat yang seharusnya.
def build_prompt(query: str, context: List[Document]) -> str:
    """Membangun prompt final dari query dan context yang didapat."""

    context_str = "\n".join([doc.page_content for doc in context])
    prompt = f"""
    Answer the following question: "{query}"
    Only use the information from the context below:
    ---
    {context_str}
    ---
    Answer:
    """
    return prompt

# 2. Upgrade fungsi pipeline menjadi async
async def run_rag_pipeline_async(
    query: str,
    retriever, # Objek retriever LangChain
    llm        # Objek LLM LangChain
) -> Dict[str, Any]:
    """
    Core RAG pipeline yang sekarang sepenuhnya asinkron.
    """
    # Langkah 1: Retrieve (sekarang dengan await)
    retrieved_docs = await retriever.ainvoke(query)
    
    # Langkah 2: Build Prompt (tetap sinkron, karena ini hanya manipulasi string)
    final_prompt = build_prompt(query, retrieved_docs)
    
    # Langkah 3: Generate (sekarang dengan await)
    answer_obj = await llm.ainvoke(final_prompt)
    
    return {
        "query": query,
        "answer": answer_obj.content,
        "source_documents": retrieved_docs
    }