from langgraph.prebuilt import create_react_agent
from langchain.schema import SystemMessage

from app.config.app_env import app_env
from app.adapters.llm_adapter import search_llm_provider
from app.agent_prompts.default_prompt import system_prompt
from app.utils.get_current_date import get_current_datetime_cranford

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

agent_system_prompt = f"""
    {system_prompt}
    ---
    Current date and time: {get_current_datetime_cranford()}
    ---
    Refer to the user as: {app_env.APP_USERNAME.capitalize()}
"""

graph = create_react_agent(search_llm_provider, tools=tools, state_modifier=SystemMessage(content=agent_system_prompt))


def invoke_our_graph(st_messages, callables):
    if not isinstance(callables, list):
        raise TypeError("callables must be a list")
    return graph.invoke({"messages": st_messages}, config={"callbacks": callables})
