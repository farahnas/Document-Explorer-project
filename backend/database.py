import os
import shutil
import time
import logging
from pathlib import Path
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    UnstructuredWordDocumentLoader
)
from .config import Config

class DatabaseManager:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self._ensure_directories_exist()

    def _ensure_directories_exist(self):
        """Ensure required directories exist"""
        os.makedirs(self.config.CHROMA_PATH, exist_ok=True)
        os.makedirs(self.config.DATA_PATH, exist_ok=True)
        
        # Create README if data directory is empty
        readme_path = os.path.join(self.config.DATA_PATH, "README.md")
        if not os.path.exists(readme_path):
            with open(readme_path, 'w') as f:
                f.write("# Data Directory\n\nPlace your documents here.")

    def clear_database(self) -> bool:
        """Clear the Chroma database with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if os.path.exists(self.config.CHROMA_PATH):
                    
                    if os.name == 'nt':
                        os.system(f'rmdir /s /q "{self.config.CHROMA_PATH}"')
                    else:
                        shutil.rmtree(self.config.CHROMA_PATH)
                    os.makedirs(self.config.CHROMA_PATH, exist_ok=True)
                    self.logger.info("Successfully cleared Chroma database")
                    return True
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"Failed to clear database after {max_retries} attempts: {str(e)}")
                    return False
                time.sleep(1)  
        return False

    def load_documents(self) -> List[Document]:
        """Load documents from the data directory"""
        documents = []
        supported_extensions = {
            '.pdf': PyPDFLoader,
            '.txt': TextLoader,
            '.csv': CSVLoader,
            '.docx': UnstructuredWordDocumentLoader
        }

        try:
            for file_path in Path(self.config.DATA_PATH).glob('*'):
                if file_path.name == "README.md":
                    continue
                    
                ext = file_path.suffix.lower()
                if ext in supported_extensions:
                    try:
                        loader = supported_extensions[ext](str(file_path))
                        if ext == '.pdf':
                        # PDF loader preserves page numbers automatically
                            docs = loader.load()
                        else:
                            docs = loader.load()
                        for doc in docs:
                            doc.metadata["source"] = file_path.name
                             # For non-PDF files, set page to 0
                            if 'page' not in doc.metadata:
                               doc.metadata["page"] = 0
                        documents.extend(docs)
                        self.logger.info(f"Loaded: {file_path.name}")
                    except Exception as e:
                        self.logger.warning(f"Error loading {file_path.name}: {str(e)}")
            return documents
        except Exception as e:
            self.logger.error(f"Document loading failed: {str(e)}")
            return []

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=80,
            length_function=len,
        )
        return text_splitter.split_documents(documents)

    def add_to_chroma(self, chunks: List[Document], embedding_function) -> bool:
        """Add documents to Chroma vectorstore"""
        try:
            
         for i, chunk in enumerate(chunks):
            source = chunk.metadata.get("source", "unknown")
            page = chunk.metadata.get("page", 0)
            chunk.metadata["source_info"] = f"{source} (page {page+1})"  
            
            db = Chroma.from_documents(
                documents=chunks,
                embedding=embedding_function,
                persist_directory=str(self.config.CHROMA_PATH)
            )
            db.persist()
            self.logger.info(f"Added {len(chunks)} chunks to Chroma")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add to Chroma: {str(e)}")
            return False

    def populate_database(self, reset: bool = False, embedding_function=None) -> bool:
        """Main method to populate the vector database"""
        try:
            self.logger.info(f"Starting database population (reset={reset})")
            
            if reset:
                self.logger.info("Attempting database reset...")
                if not self.clear_database():
                    self.logger.error("Database reset failed")
                    return False
                self.logger.info("Database reset successful")

            self.logger.info("Loading documents...")
            documents = self.load_documents()
            if not documents:
                self.logger.error("No documents loaded - check data directory")
                return False
            self.logger.info(f"Loaded {len(documents)} documents")

            self.logger.info("Splitting documents...")
            chunks = self.split_documents(documents)
            if not chunks:
                self.logger.error("No chunks created from documents")
                return False
            self.logger.info(f"Created {len(chunks)} chunks")

            self.logger.info("Adding to Chroma...")
            result = self.add_to_chroma(chunks, embedding_function)
            self.logger.info(f"Chroma addition result: {result}")
            return result
            if reset and not self.clear_database():
               return {"success": False, "message": "Reset failed"}
            
            documents = self.load_documents()
            if not documents:
               return {"success": False, "message": "No documents found"}
            
            chunks = self.split_documents(documents)
            if not chunks:
               return {"success": False, "message": "No chunks created"}
            
            success = self.add_to_chroma(chunks, embedding_function)
            return {
            "success": success,
            "document_count": len(documents),
            "chunk_count": len(chunks)
        }
        except Exception as e:
            self.logger.error(f"Population failed: {str(e)}", exc_info=True)
            return False 