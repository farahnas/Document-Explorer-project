from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import Callable
from .config import Config

def get_embedding_function() -> Callable:
    """Get the embedding function."""
    config = Config()
    return HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': False}
    ) 