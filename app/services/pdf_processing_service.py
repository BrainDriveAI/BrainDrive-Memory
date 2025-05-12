import uuid
import os
import PyPDF2
from google.cloud import storage
from neo4j import GraphDatabase
from app.app_env import app_env

SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "service_account.json")


def get_storage_client():
    if os.getenv("K_SERVICE") or os.getenv("FUNCTION_TARGET"):
        return storage.Client()  # Cloud Function - use default creds
    return storage.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)


# --- Helper functions ---
def generate_topics(text: str) -> list:
    """
    Dynamically generate topics based on the text.
    This is a placeholder implementation—replace with an NLP solution as needed.
    """
    topics = []
    if "work" in text.lower():
        topics.append("Work")
    if "health" in text.lower():
        topics.append("Health")
    return topics or ["General"]


def upload_file_to_gcs(file_path: str, bucket_name: str, destination_blob_name: str) -> str:
    """
    Uploads a file to Google Cloud Storage and returns its public URL.
    """
    storage_client = get_storage_client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path, content_type="application/pdf")
    # Make file public or configure ACLs appropriately
    # blob.make_public()
    return blob.public_url


def extract_pdf_metadata(pdf_file_path: str) -> dict:
    """
    Extracts basic metadata from a PDF file.
    """
    metadata = {}
    try:
        with open(pdf_file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            metadata['num_pages'] = len(reader.pages)
            pdf_info = reader.metadata
            metadata['title'] = pdf_info.title if pdf_info and pdf_info.title else os.path.basename(pdf_file_path)
            metadata['author'] = pdf_info.author if pdf_info and pdf_info.author else ""
    except Exception as e:
        print(f"Error extracting metadata: {e}")
    return metadata


def extract_pdf_text(pdf_file_path: str) -> str:
    """
    Extracts the full text from a PDF file.
    """
    full_text = ""
    try:
        with open(pdf_file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
    except Exception as e:
        print(f"Error extracting text: {e}")
    return full_text


def chunk_text(text: str, chunk_size: int = 500) -> list:
    """
    Splits the text into chunks of roughly 'chunk_size' characters.
    These chunks can later be embedded and stored in a vector store.
    """
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


# --- Neo4j File Manager Class ---
class Neo4jFileManager:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()

    def create_file_node(self, file_id: str, file_name: str, file_type: str, cloud_url: str, metadata: dict, topics: list):
        """
        Creates (or updates) a File node in Neo4j with associated topics.
        """
        query = """
        MERGE (f:File {file_id: $file_id})
        SET f.name = $file_name,
            f.file_name = $file_name,
            f.file_type = $file_type,
            f.user_id = $author,
            f.cloud_url = $cloud_url
        WITH f
        UNWIND $topics as topic
        MERGE (t:FileCategory {name: topic})
        MERGE (f)-[:BELONGS_TO]->(t)
        WITH f
        SET f.title = $title,
            f.user_id = $author,
            f.num_pages = $num_pages
        RETURN f
        """
        with self.driver.session() as session:
            result = session.run(
                query,
                file_id=file_id,
                file_name=file_name,
                file_type=file_type,
                cloud_url=cloud_url,
                topics=topics,
                title=metadata.get('title', ''),
                author=app_env.APP_USERNAME,
                num_pages=metadata.get('num_pages', 0)
            )
            return result.single()


# --- Process PDF Upload Function ---
def process_pdf_upload(pdf_file_path: str, bucket_name: str, neo4j_manager: Neo4jFileManager):
    """
    Processes a PDF file:
      - Extracts metadata and full text.
      - Uploads the PDF to Google Cloud Storage.
      - Dynamically generates topics from the file's content.
      - Creates a file node in Neo4j with general metadata.
      - Chunks the file text for semantic (vector) indexing.
    
    Returns a dictionary with the file information.
    """
    # Extract metadata and text from the PDF
    pdf_metadata = extract_pdf_metadata(pdf_file_path)
    full_text = extract_pdf_text(pdf_file_path)
    
    # Generate a unique file ID
    file_id = str(uuid.uuid4())
    file_name = os.path.basename(pdf_file_path)
    file_type = "pdf"
    
    # Upload file to Google Cloud Storage
    destination_blob_name = f"uploads/{file_id}_{file_name}"
    cloud_url = upload_file_to_gcs(pdf_file_path, bucket_name, destination_blob_name)
    
    # Dynamically generate topics from the file content
    topics = generate_topics(full_text)
    
    # Create a File node in Neo4j with the metadata and topics
    neo4j_manager.create_file_node(
        file_id=file_id,
        file_name=file_name,
        file_type=file_type,
        cloud_url=cloud_url,
        metadata=pdf_metadata,
        topics=topics
    )
    
    # Chunk the full text (for indexing in a vector store if needed)
    chunks = chunk_text(full_text)
    
    # Return the file information (metadata is general to allow export without personal data)
    file_info = {
        "file_id": file_id,
        "file_name": file_name,
        "file_type": file_type,
        "cloud_url": cloud_url,
        "metadata": pdf_metadata,
        "topics": topics,
        "chunks": chunks  # Use these chunks for further semantic indexing
    }
    return file_info

# # --- Example Usage ---
#
# if __name__ == "__main__":
#     # Set your Google Cloud bucket name
#     BUCKET_NAME = "your-google-cloud-bucket-name"
#
#     # Initialize the Neo4jFileManager with your connection details
#     NEO4J_URI = "bolt://localhost:7687"
#     NEO4J_USER = "neo4j"
#     NEO4J_PASSWORD = "your-neo4j-password"
#
#     neo4j_manager = Neo4jFileManager(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
#
#     # Path to the PDF file to be uploaded
#     pdf_path = "path/to/your/document.pdf"
#
#     # Process the file upload
#     file_info = process_pdf_upload(pdf_path, BUCKET_NAME, neo4j_manager)
#     print("File processed and uploaded:")
#     print(file_info)
#
#     neo4j_manager.close()
