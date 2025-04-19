from langchain.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
from typing import Dict
from .config import Config
import logging

class Model:
    def __init__(self):
        self.config = Config()
        try:
            self.model = Ollama(
                model=self.config.LLM_MODEL,
                base_url='http://localhost:11434',
                timeout=300,
                temperature=0.7
            )
            # Test connection
            test_response = self.model.invoke("Test connection")
            logging.info("Model initialized successfully")
            
            self.prompt_template = ChatPromptTemplate.from_template(self.config.PROMPT_TEMPLATE)
        except Exception as e:
            logging.error(f"Model initialization failed: {str(e)}")
            raise

    def query_database(self, query_text: str, db) -> Dict:
        """Query the database and generate a response."""
        try:
            results = db.similarity_search_with_score(query_text, k=5)
            if not results:
                return {"response": "No relevant information found", "sources": []}

            context_text = "\n\n---\n\n".join([doc.page_content for doc, _ in results])
            response_text = self.model.invoke(self.prompt_template.format(
                context=context_text,
                question=query_text
            ))
            
            sources = list(set([
            doc.metadata.get("source_info", 
            f"{doc.metadata.get('source', 'unknown')} (page {int(doc.metadata.get('page', 0))+1})")
            for doc, _ in results
        ]))
        
            
            return {
                "response": response_text.strip(),
                "sources": sources
            }
        except Exception as e:
            logging.error(f"Query error: {str(e)}")
            return {"response": f"Error: {str(e)}", "sources": []}
     