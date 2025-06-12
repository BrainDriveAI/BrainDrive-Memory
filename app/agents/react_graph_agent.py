from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.adapters.llm_adapter import search_llm_provider
from app.agent_prompts.system_prompt_manager import SystemPromptManager

from app.tools.search.search_tool import search_for_memories
from app.tools.add.add_tool import add_graph_memory
from app.tools.get_all.get_all_tool import get_all_items
from app.tools.update.update_tool import update_graph_memory
from app.tools.delete.delete_tool import delete_graph_memory
from app.tools.documents_search.documents_search_tool import search_for_doc_snippets, search_for_documents

tools = [
    search_for_memories,
    add_graph_memory,
    get_all_items,
    update_graph_memory,
    delete_graph_memory,
    search_for_doc_snippets,
    search_for_documents,
]

# Get the appropriate system prompt
agent_system_prompt = SystemPromptManager.get_system_prompt()

checkpointer = InMemorySaver()

graph = create_react_agent(
    search_llm_provider,
    tools=tools,
    prompt=agent_system_prompt,
    checkpointer=checkpointer,
)


def invoke_our_graph(st_messages, callables):
    if not isinstance(callables, list):
        raise TypeError("callables must be a list")
    return graph.invoke({"messages": st_messages}, config={"callbacks": callables, "recursion_limit": 10, "configurable": {"thread_id": "1"}})
