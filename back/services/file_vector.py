import os
import json
import logging
import datetime
from typing import Dict, Any, List, Optional

# Milvus Lite imports
from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType

class VectorFileProcessor:
    """
    Service for managing and retrieving statistics about vector embedding files
    and storing them into vector databases.
    """
    def __init__(self):
        self.embedding_folder = os.path.join('files', 'embedding')
        self.db_folder = os.path.join('files', 'db') # For Milvus Lite DB file
        os.makedirs(self.embedding_folder, exist_ok=True)
        os.makedirs(self.db_folder, exist_ok=True) # Ensure db folder exists
        self.logger = logging.getLogger(__name__)
        self.milvus_lite_uri = os.path.join(self.db_folder, "milvus_lite.db")

    def _connect_milvus_lite(self):
        """Establishes connection to Milvus Lite."""
        try:
            self.logger.info(f"Attempting to connect to Milvus Lite at: {self.milvus_lite_uri}")
            connections.connect(alias="default", uri=self.milvus_lite_uri)
            self.logger.info("Successfully connected to Milvus Lite.")
        except Exception as e:
            self.logger.error(f"Failed to connect to Milvus Lite: {e}", exc_info=True)
            raise

    def _disconnect_milvus_lite(self):
        """Disconnects from Milvus Lite if connected."""
        try:
            if "default" in connections.list_connections():
                connections.disconnect(alias="default")
                self.logger.info("Successfully disconnected from Milvus Lite.")
        except Exception as e:
            self.logger.error(f"Error disconnecting from Milvus Lite: {e}", exc_info=True)

    def get_all_vector_file_stats(self) -> Dict[str, Any]:
        """
        Retrieves statistics for all vector embedding files (.json)
        in the embedding folder.

        Returns:
            Dict: A dictionary containing a success flag and a list of file statistics.
        """
        all_file_stats = []
        if not os.path.exists(self.embedding_folder):
            self.logger.warning(f"Embedding folder not found: {self.embedding_folder}")
            return {
                "success": False,
                "error": f"Embedding folder '{self.embedding_folder}' not found.",
                "files": []
            }

        try:
            for filename in os.listdir(self.embedding_folder):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.embedding_folder, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            file_data = json.load(f)
                        
                        metadata = file_data.get("embedding_metadata", {})
                        
                        # Try to get original file ID, fallback to a modified filename
                        original_file_id = metadata.get("chunk_file_id")
                        if not original_file_id:
                             # Attempt to derive from filename if chunk_file_id is missing
                            if filename.endswith("_embedded.json"):
                                original_file_id = filename[:-len("_embedded.json")]
                            else:
                                original_file_id = filename[:-len(".json")]


                        file_stat = {
                            "vector_file_name": filename,
                            "original_file_id": original_file_id,
                            "model_type": metadata.get("embedding_model_type", "N/A"),
                            "model_name": metadata.get("embedding_model_name", "N/A"),
                            "model_dim": metadata.get("embedding_model_dim", "N/A"),
                            "processed_chunks": metadata.get("processed_chunk_count", "N/A"),
                            "total_chunks": metadata.get("total_chunk_count", "N/A"),
                            "embedding_time_seconds": metadata.get("embedding_time_seconds", "N/A"),
                            "created_at": metadata.get("embedding_timestamp", "N/A"),
                            "file_size_bytes": os.path.getsize(filepath),
                            "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                        }
                        all_file_stats.append(file_stat)
                    except json.JSONDecodeError as json_err:
                        self.logger.error(f"Error decoding JSON from file {filepath}: {json_err}")
                        all_file_stats.append({
                            "vector_file_name": filename,
                            "error": f"Invalid JSON format: {str(json_err)}",
                            "file_size_bytes": os.path.getsize(filepath)
                        })
                    except Exception as e:
                        self.logger.error(f"Error processing vector file {filepath}: {e}", exc_info=True)
                        all_file_stats.append({
                            "vector_file_name": filename,
                            "error": f"Failed to process: {str(e)}",
                            "file_size_bytes": os.path.getsize(filepath)
                        })
            
            self.logger.info(f"Successfully retrieved stats for {len(all_file_stats)} vector files.")
            return {
                "success": True,
                "files": all_file_stats,
                "timestamp": datetime.datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to list or access embedding folder {self.embedding_folder}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"An unexpected error occurred while accessing vector files: {str(e)}",
                "files": []
            }

    def store_vectors_to_milvus_lite(
        self, 
        embedding_file_id: str, 
        collection_name: str, 
        dimension: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Loads vectors from an embedding file and stores them into Milvus Lite.

        Args:
            embedding_file_id: The name of the _embedded.json file.
            collection_name: The name for the Milvus collection.
            dimension: The embedding dimension. If None, tries to infer from the first chunk.

        Returns:
            A dictionary with success status and details.
        """
        self.logger.info(f"Starting vector storage to Milvus Lite for file: {embedding_file_id}, collection: {collection_name}")
        
        embedding_filepath = os.path.join(self.embedding_folder, embedding_file_id)
        if not os.path.exists(embedding_filepath):
            self.logger.error(f"Embedding file not found: {embedding_filepath}")
            return {"success": False, "error": f"Embedding file '{embedding_file_id}' not found."}

        try:
            with open(embedding_filepath, 'r', encoding='utf-8') as f:
                embedding_data = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to read or parse embedding file {embedding_filepath}: {e}", exc_info=True)
            return {"success": False, "error": f"Error reading embedding file: {str(e)}"}

        chunks = embedding_data.get("chunks", [])
        file_metadata = embedding_data.get("embedding_metadata", {})
        
        if not chunks:
            self.logger.warning(f"No chunks found in {embedding_file_id}")
            return {"success": False, "error": "No chunks found in the embedding file."}

        # Infer dimension if not provided
        if dimension is None:
            if chunks[0].get("embedding"):
                dimension = len(chunks[0]["embedding"])
                self.logger.info(f"Inferred embedding dimension: {dimension}")
            else:
                self.logger.error("Dimension not provided and could not be inferred from the first chunk.")
                return {"success": False, "error": "Embedding dimension is required and could not be inferred."}
        
        if not isinstance(dimension, int) or dimension <= 0:
            self.logger.error(f"Invalid dimension provided or inferred: {dimension}")
            return {"success": False, "error": f"Invalid embedding dimension: {dimension}"}

        try:
            self._connect_milvus_lite()

            # Define schema
            # Use VARCHAR for chunk_id to allow for more flexible IDs from the source
            # Keep original_doc_id to link back to the source document file
            field_id = FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True)
            field_embedding = FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension)
            field_text_content = FieldSchema(name="text_content", dtype=DataType.VARCHAR, max_length=65535) # Max length for VARCHAR
            field_original_doc_id = FieldSchema(name="original_doc_id", dtype=DataType.VARCHAR, max_length=1024) # e.g. the chunk_file_id from embedding_metadata
            field_chunk_seq_num = FieldSchema(name="chunk_seq_num", dtype=DataType.INT64) # Sequence number of the chunk within the doc
            
            schema = CollectionSchema(
                fields=[field_id, field_embedding, field_text_content, field_original_doc_id, field_chunk_seq_num],
                description=f"Collection for document chunks from {file_metadata.get('chunk_file_id', 'unknown_source')}",
                enable_dynamic_field=False # Set to True if you want to add other metadata ad-hoc
            )

            if utility.has_collection(collection_name, using='default'):
                self.logger.info(f"Collection '{collection_name}' already exists. Using existing collection.")
                collection = Collection(collection_name, using='default')
                # Consider checking if schema matches, or if it needs to be dropped and recreated
                # For simplicity, we'll assume it's compatible or the user manages this.
            else:
                self.logger.info(f"Creating new collection: '{collection_name}'")
                collection = Collection(collection_name, schema=schema, using='default', consistency_level="Strong") # Bounded for Lite
                self.logger.info(f"Collection '{collection_name}' created successfully.")

            # Prepare data for insertion
            data_to_insert = []
            for idx, chunk in enumerate(chunks):
                embedding_vector = chunk.get("embedding")
                content = chunk.get("content", "")
                
                if not embedding_vector or len(embedding_vector) != dimension:
                    self.logger.warning(f"Skipping chunk {idx} due to missing or mismatched dimension embedding.")
                    continue
                
                data_to_insert.append({
                    "embedding": embedding_vector,
                    "text_content": content[:65534], # Ensure it fits VARCHAR
                    "original_doc_id": file_metadata.get("chunk_file_id", "N/A"),
                    "chunk_seq_num": chunk.get("chunk_id", idx) # Use chunk_id if present, else sequence
                })

            if not data_to_insert:
                self.logger.warning("No valid data prepared for insertion.")
                return {"success": False, "error": "No valid chunks with embeddings found for insertion."}

            insert_result = collection.insert(data_to_insert)
            collection.flush() # Ensure data is written
            self.logger.info(f"Successfully inserted {len(insert_result.primary_keys)} vectors into '{collection_name}'.")

            # Create index if it doesn't exist for the embedding field
            # This is crucial for search performance
            index_exists = False
            for index in collection.indexes:
                if index.field_name == "embedding":
                    index_exists = True
                    self.logger.info(f"Index on 'embedding' field already exists for collection '{collection_name}'.")
                    break
            
            if not index_exists:
                self.logger.info(f"Creating index for 'embedding' field in collection '{collection_name}'.")
                # IVF_FLAT is a common choice, HNSW is another good option.
                # Adjust nlist based on expected data size. Default 128.
                index_params = { 
                    "metric_type": "L2",  # Or "IP" for inner product, depending on embedding model
                    "index_type": "IVF_FLAT", 
                    "params": {"nlist": 128}
                }
                collection.create_index(field_name="embedding", index_params=index_params)
                self.logger.info(f"Index created successfully for '{collection_name}'.")

            collection.load() # Load collection into memory for searching

            milvus_version_str = "N/A"
            try:
                milvus_version_str = utility.get_server_version()
            except Exception as ver_exc:
                self.logger.warning(f"Could not retrieve Milvus server version: {ver_exc}")
                milvus_version_str = "N/A (RPC GetVersion unimplemented or error)"

            return {
                "success": True,
                "message": f"Successfully stored {len(insert_result.primary_keys)} vectors into Milvus Lite collection '{collection_name}'.",
                "details": {
                    "collection_name": collection_name,
                    "vectors_inserted": len(insert_result.primary_keys),
                    "total_chunks_in_file": len(chunks),
                    "db_path": self.milvus_lite_uri,
                    "milvus_version": milvus_version_str
                }
            }

        except Exception as e:
            self.logger.error(f"Error during Milvus Lite operation: {e}", exc_info=True)
            return {"success": False, "error": f"Milvus Lite operation failed: {str(e)}"}
        finally:
            self._disconnect_milvus_lite()

if __name__ == '__main__':
    # Basic test for the service
    logging.basicConfig(level=logging.INFO)
    processor = VectorFileProcessor()
    # Create dummy files for testing
    dummy_folder = os.path.join('files', 'embedding')
    os.makedirs(dummy_folder, exist_ok=True)
    
    dummy_data_1 = {
        "embedding_metadata": {
            "chunk_file_id": "test_doc_1",
            "embedding_model_type": "huggingface",
            "embedding_model_name": "bge-small-zh",
            "embedding_model_dim": 512,
            "processed_chunk_count": 10,
            "total_chunk_count": 10,
            "embedding_time_seconds": 5.0,
            "embedding_timestamp": datetime.datetime.now().isoformat()
        },
        "chunks": []
    }
    with open(os.path.join(dummy_folder, "test_doc_1_embedded.json"), "w") as f:
        json.dump(dummy_data_1, f)

    dummy_data_2 = {
         "embedding_metadata": {
            "chunk_file_id": "another_document_abc",
            "embedding_model_type": "openai",
            "embedding_model_name": "text-embedding-3-small",
            "embedding_model_dim": 1536,
            "processed_chunk_count": 5,
            "total_chunk_count": 5,
            "embedding_time_seconds": 2.1,
            "embedding_timestamp": datetime.datetime.now().isoformat()
        },
        "chunks": []
    }
    with open(os.path.join(dummy_folder, "another_document_abc_embedded.json"), "w") as f:
        json.dump(dummy_data_2, f)

    with open(os.path.join(dummy_folder, "invalid_file.json"), "w") as f:
        f.write("this is not json")

    stats_result = processor.get_all_vector_file_stats()
    print(json.dumps(stats_result, indent=2))

    # Clean up dummy files
    # os.remove(os.path.join(dummy_folder, "test_doc_1_embedded.json"))
    # os.remove(os.path.join(dummy_folder, "another_document_abc_embedded.json"))
    # os.remove(os.path.join(dummy_folder, "invalid_file.json")) 