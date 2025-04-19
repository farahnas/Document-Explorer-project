import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from flask import Flask, render_template, request, jsonify
import os
import logging
from backend.database import DatabaseManager
from backend.embeddings import get_embedding_function
from backend.models import Model
from backend.config import Config
from langchain_community.vectorstores import Chroma
app = Flask(__name__)
config = Config()
from backend.database import DatabaseManager
db_manager = DatabaseManager()  
app.config['UPLOAD_FOLDER'] = str(config.DATA_PATH)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, jsonify
import os
import logging
from backend.database import DatabaseManager
from backend.embeddings import get_embedding_function
from backend.models import Model
from backend.config import Config
from langchain_community.vectorstores import Chroma

app = Flask(__name__)
config = Config()

# Configuration
app.config['UPLOAD_FOLDER'] = str(config.DATA_PATH)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize components
embedding_function = get_embedding_function()
db_manager = DatabaseManager()
guide_model = Model()

@app.route('/health')
def health_check():
    try:
        # Check Chroma
        db = Chroma(
            persist_directory=str(config.CHROMA_PATH),
            embedding_function=embedding_function
        )
        count = len(db.get()['ids']) if db.get()['ids'] else 0
        
        return jsonify({
            "status": "healthy",
            "chroma": "connected",
            "documents": count
        })
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500
# Initialize components
embedding_function = get_embedding_function()
db_manager = DatabaseManager()
guide_model = Model()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files selected"}), 400

    saved_files = []
    for file in files:
        if file.filename == '':
            continue
        if Path(file.filename).suffix.lower()[1:] not in config.ALLOWED_EXTENSIONS:
            continue
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        saved_files.append(file.filename)

    return jsonify({
        "success": True,
        "message": f"{len(saved_files)} files uploaded successfully",
        "files": saved_files
    })

@app.route('/populate', methods=['POST'])
def populate_database():
    try:
        reset = request.json.get('reset', False)
        success = db_manager.populate_database(reset=reset, embedding_function=embedding_function)
        
        if success:
            db = Chroma(
                persist_directory=str(config.CHROMA_PATH),
                embedding_function=embedding_function
            )
            count = len(db.get()['ids']) if db.get()['ids'] else 0
            
            return jsonify({
                "success": True,
                "message": f"Database populated successfully with {count} chunks",
                "document_count": len(os.listdir(config.DATA_PATH)) - 1,  # Subtract README.md
                "chunk_count": count
            })
        return jsonify({
            "success": False,
            "message": "Database population failed (check logs)"
        }), 400
    except Exception as e:
        logging.error(f"Population error: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    except Exception as e:
        logging.error(f"Population error: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
@app.route('/query', methods=['POST'])
def query():
    try:
        question = request.json.get('question', '').strip()
        if not question:
            return jsonify({"error": "No question provided"}), 400

        # Initialize Chroma with error handling
        try:
            db = Chroma(
                persist_directory=str(config.CHROMA_PATH),
                embedding_function=embedding_function
            )
        except Exception as e:
            logging.error(f"Chroma initialization error: {str(e)}")
            return jsonify({
                "error": "Database connection failed",
                "details": str(e)
            }), 500

        # Verify database content
        db_content = db.get()
        if not db_content.get('ids'):
            return jsonify({
                "response": "Database is empty. Please upload and populate documents first.",
                "sources": []
            })

        # Test embedding function
        try:
            test_embedding = embedding_function.embed_query("test")
            if not test_embedding:
                raise ValueError("Embedding failed")
        except Exception as e:
            logging.error(f"Embedding test failed: {str(e)}")
            return jsonify({
                "error": "Embedding service failed",
                "details": str(e)
            }), 500

        # Process query
        try:
            result = guide_model.query_database(question, db)
            return jsonify({
                "success": True,
                "response": result["response"],
                "sources": result["sources"]
            })
        except Exception as e:
            logging.error(f"Query processing failed: {str(e)}", exc_info=True)
            return jsonify({
                "error": "Query processing failed",
                "details": str(e)
            }), 500

    except Exception as e:
        logging.error(f"Unexpected query error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Unknown error occurred",
            "details": str(e)
        }), 500
    
@app.route('/test')
def test_pipeline():
    test_text = "This is a test document about ancient Egypt."
    test_embedding = embedding_function.embed_query(test_text)
    return jsonify({
        "embedding_works": bool(test_embedding),
        "embedding_length": len(test_embedding) if test_embedding else 0
    })
@app.route('/list-documents')
def list_documents():
    try:
        files = [f for f in os.listdir(config.DATA_PATH) if f != 'README.md']
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)