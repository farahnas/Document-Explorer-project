from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class Config:
    CHROMA_PATH = BASE_DIR / "chroma_db"
    DATA_PATH = BASE_DIR / "data"
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'csv', 'docx'}
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    LLM_MODEL = "mistral"
    PROMPT_TEMPLATE = """
    You are a helpful assistant that provides information based on the following context:

    {context}

    ---

    Question: {question}

    Provide a detailed, accurate response in a professional tone. 
    If you don't know the answer, say you don't know rather than making something up.
    """
    
    def __init__(self):
        self.CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        self.DATA_PATH.mkdir(parents=True, exist_ok=True) 