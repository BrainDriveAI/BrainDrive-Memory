import threading
import time
from app.config.app_env import app_env
from typing import Any, Dict, List, Optional

try:
    from langchain_neo4j import Neo4jGraph
except ImportError:
    raise ImportError("langchain_neo4j is not installed. Please install it using pip install langchain_neo4j")

from app.interfaces.graph_db_interface import GraphDBInterface

class Neo4jAdapter(GraphDBInterface):
    """
    Thread-safe Neo4j adapter that replaces your existing one.
    Uses thread-local storage to prevent connection conflicts.
    
    This is a DROP-IN REPLACEMENT - no changes needed elsewhere in your code!
    """
    
    def __init__(self, url: Optional[str] = None, username: Optional[str] = None, 
                 password: Optional[str] = None, database: Optional[str] = None):
        # Store connection parameters
        self.url = url or app_env.NEO4J_URL
        self.username = username or app_env.NEO4J_USER
        self.password = password or app_env.NEO4J_PWD.get_secret_value()
        self.database = database or app_env.NEO4J_DATABASE
        
        # Thread-local storage for Neo4jGraph instances
        self._local = threading.local()
        
        # Semaphore to limit concurrent operations (prevents pool exhaustion)
        self._semaphore = threading.Semaphore(5)  # Max 5 concurrent operations
        
        print(f"[Neo4jAdapter] Initialized thread-safe adapter for {self.url}")
    
    def _get_graph_instance(self) -> Neo4jGraph:
        """
        Get or create a thread-local Neo4jGraph instance.
        Each thread gets its own instance to avoid connection conflicts.
        """
        if not hasattr(self._local, 'graph') or self._local.graph is None:
            thread_name = threading.current_thread().name
            print(f"[Neo4jAdapter] Creating new Neo4jGraph instance for thread: {thread_name}")
            
            self._local.graph = Neo4jGraph(
                url=self.url,
                username=self.username,
                password=self.password,
                database=self.database
            )
        
        return self._local.graph
    
    def query(self, cypher_query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute Cypher query with connection limiting and retry logic.
        
        Features:
        - Connection limiting via semaphore
        - Automatic retry on connection errors
        - Thread-local Neo4jGraph instances
        - Exponential backoff on retries
        """
        # Limit concurrent operations to prevent connection pool exhaustion
        with self._semaphore:
            return self._execute_query_with_retry(cypher_query, params or {})
    
    def _execute_query_with_retry(self, cypher_query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute query with retry logic for connection errors."""
        max_retries = 3
        retry_delay = 1
        thread_name = threading.current_thread().name
        
        for attempt in range(max_retries):
            try:
                graph = self._get_graph_instance()
                result = graph.query(cypher_query, params)
                
                # Success - log if this was a retry
                if attempt > 0:
                    print(f"[Neo4jAdapter] Query succeeded on attempt {attempt + 1} for thread: {thread_name}")
                
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a connection-related error
                is_connection_error = any(keyword in error_msg for keyword in [
                    'connection aborted', 'remote disconnected', 
                    'connection reset', 'connection timeout',
                    'connection refused', 'network unreachable'
                ])
                
                if is_connection_error and attempt < max_retries - 1:
                    print(f"[Neo4jAdapter] Connection error on attempt {attempt + 1} "
                          f"for thread {thread_name}: {e}")
                    print(f"[Neo4jAdapter] Retrying in {retry_delay} seconds...")
                    
                    # Clear the thread-local graph to force reconnection
                    self._clear_thread_local_graph()
                    
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff: 1s, 2s, 4s
                    
                elif is_connection_error:
                    # Max retries exceeded for connection error
                    print(f"[Neo4jAdapter] Max retries exceeded for thread {thread_name}. "
                          f"Final connection error: {e}")
                    raise Exception(f"Neo4j connection failed after {max_retries} attempts: {e}")
                    
                else:
                    # Non-connection error (syntax, permissions, etc.) - don't retry
                    print(f"[Neo4jAdapter] Non-connection error for thread {thread_name}: {e}")
                    raise e
        
        return []  # Fallback (shouldn't reach here)
    
    def _clear_thread_local_graph(self):
        """Clear the thread-local graph instance to force reconnection."""
        if hasattr(self._local, 'graph'):
            try:
                # Try to close the existing connection gracefully
                if hasattr(self._local.graph, '_driver') and self._local.graph._driver:
                    self._local.graph._driver.close()
            except:
                pass  # Ignore errors during cleanup
            finally:
                self._local.graph = None
    
    def close(self):
        """
        Clean up resources. Call this when shutting down your application.
        """
        print("[Neo4jAdapter] Closing adapter...")
        self._clear_thread_local_graph()
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Debug method to get connection information.
        Useful for monitoring and troubleshooting.
        """
        thread_name = threading.current_thread().name
        has_local_graph = hasattr(self._local, 'graph') and self._local.graph is not None
        
        return {
            "thread_name": thread_name,
            "has_local_graph_instance": has_local_graph,
            "semaphore_available": self._semaphore._value,
            "url": self.url,
            "database": self.database
        }

# Optional: Add monitoring/debugging utilities
class Neo4jAdapterMonitor:
    """
    Optional utility class for monitoring Neo4j adapter performance.
    """
    
    @staticmethod
    def log_connection_info(adapter: Neo4jAdapter):
        """Log current connection information."""
        info = adapter.get_connection_info()
        print(f"[Neo4jAdapter Monitor] {info}")
    
    @staticmethod
    def test_connection(adapter: Neo4jAdapter) -> bool:
        """Test if the adapter can successfully connect."""
        try:
            result = adapter.query("RETURN 1 as test", {})
            return len(result) > 0 and result[0].get('test') == 1
        except Exception as e:
            print(f"[Neo4jAdapter Monitor] Connection test failed: {e}")
            return False
