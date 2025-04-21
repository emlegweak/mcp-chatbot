import os
from helpers import load_config_with_env
from core import Configuration, Server, LLMClient, ChatSession
from vector_stores.factory import get_vector_store
from vector_stores.loaders.factory import get_document_loader


def create_chat_session() -> ChatSession:
    """
    Initializes and returns a ChatSession instance configured with MCP servers, 
    LLM Client, and optional vector store support for retrieval-augmented generation.

    Returns:
        ChatSession: A ChatSession instance for handling multi-turn user conversations, 
        tool invocation, and contextual response generation.
    """
    config = Configuration()
    server_config = load_config_with_env('servers_config.json')
    servers = [Server(name, srv_config)
               for name, srv_config in server_config['mcpServers'].items()]
    llm_client = LLMClient(
        provider=config.provider,
        api_key=config.api_key,
        model=config.model,
        endpoint=config.endpoint
    )
    vector_store_provider = os.getenv("VECTOR_STORE_PROVIDER", None)
    vector_data_path = os.getenv("VECTOR_STORE_PATH", None)
    vector_data_format = os.getenv("VECTOR_STORE_FORMAT", None)
    document_loader = get_document_loader(vector_data_format)
    vector_store = get_vector_store(
        vector_store_provider, loader=document_loader, path=vector_data_path)
    return ChatSession(servers, llm_client, vector_store)
