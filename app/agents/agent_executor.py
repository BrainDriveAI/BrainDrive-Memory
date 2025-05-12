from typing import List, Tuple

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from langchain.schema import AIMessage, HumanMessage
from langchain_core.utils.function_calling import convert_to_openai_function

from app.app_env import app_env
from app.adapters.llm_adapter import search_llm_provider
from app.agent_prompts.custom_prompt import system_prompt
from app.utils.get_current_date import get_current_datetime_cranford

from app.tools.search.search_tool import SearchForMemoryItemsTool
from app.tools.add.add_tool import AddGraphMemoryTool
from app.tools.get_all.get_all_tool import GetAllMemoryItemsTool
from app.tools.update.update_tool import UpdateGraphMemoryTool
from app.tools.delete.delete_tool import DeleteGraphMemoryTool
from app.tools.documents_search.documents_search_tool import SearchForDocumentSnippetsTool, SearchForDocumentsTool

tools = [
    SearchForMemoryItemsTool(),
    AddGraphMemoryTool(),
    GetAllMemoryItemsTool(),
    UpdateGraphMemoryTool(),
    DeleteGraphMemoryTool(),
    SearchForDocumentSnippetsTool(),
    SearchForDocumentsTool()
]

llm_with_tools = search_llm_provider.bind(functions=[convert_to_openai_function(t) for t in tools])

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"""
            {system_prompt}
            ---
            Current date and time in Cranford, NJ: {get_current_datetime_cranford()}
            ---
            Refer to user by user name:  {app_env.APP_USERNAME}
            """
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


def _format_chat_history(chat_history: List[Tuple[str, str]]):
    buffer = []
    for human, ai in chat_history:
        buffer.append(HumanMessage(content=human))
        buffer.append(AIMessage(content=ai))
    return buffer


agent = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: x["chat_history"]
        if x.get("chat_history")
        else [],
        "agent_scratchpad": lambda x: format_to_openai_function_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIFunctionsAgentOutputParser()
)


# Add typing for input
class AgentInput(BaseModel):
    input: str
    chat_history: List[Tuple[str, str]] = Field(
        ..., extra={"widget": {"type": "chat", "input": "input", "output": "output"}}
    )


agent_executor = AgentExecutor(
    agent=agent,
    verbose=True,
    tools=tools).with_types(
    input_type=AgentInput,
)


# --- New helper functions for summarization-based pruning ---
def summarize_conversation(messages: List[Tuple[str, str]]) -> str:
    """
    Summarize a list of conversation turns into a concise summary.
    """
    # Combine the conversation into a text block.
    conversation_turns = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            conversation_turns.append(f"User: {msg.content}")
        elif isinstance(msg, AIMessage):
            conversation_turns.append(f"Assistant: {msg.content}")
    conversation = "\n".join(conversation_turns)
    summarization_prompt = (
        f"Please provide a concise summary of the following conversation:\n\n{conversation}\n\nSummary:"
    )
    summary_response = search_llm_provider.invoke(summarization_prompt)
    if isinstance(summary_response, AIMessage):
        return summary_response.content
    elif isinstance(summary_response, dict) and "content" in summary_response:
        return summary_response["content"]
    else:
        return "Summary not available."


def prune_chat_history(chat_history: List[Tuple[str, str]], threshold: int = 8) -> List[Tuple[str, str]]:
    """
    If the chat history exceeds the threshold, summarize the older messages and
    retain only the most recent interactions in full.
    """
    if len(chat_history) <= threshold:
        return chat_history

    # Summarize all messages except for the last two interactions.
    to_summarize = chat_history[:-2]
    summarized_text = summarize_conversation(to_summarize)
    # Replace the old messages with a single summary entry.
    pruned_history = [AIMessage(content=summarized_text)] + chat_history[-2:]
    return pruned_history


async def invoke_memory_agent(latest_prompt: str, chat_history=None):
    if chat_history is None:
        chat_history = []
    pruned_history = prune_chat_history(chat_history)
    return await agent_executor.ainvoke({"input": latest_prompt, "chat_history": pruned_history})
