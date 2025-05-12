from app.tools.shared_utils.prompts import DELETE_RELATIONS_SYSTEM_PROMPT
from app.adapters.llm_adapter import search_llm_provider
from app.logger import app_logger as logger
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate


def get_delete_messages(existing_memories_string, data, user_id):
    return DELETE_RELATIONS_SYSTEM_PROMPT.replace(
        "USER_ID", user_id
    ), f"Here are the existing memories: {existing_memories_string} \n\n New Information: {data}"


def format_entities(entities):
    if not entities:
        return ""

    formatted_lines = []
    for entity in entities:
        simplified = f"{entity['source']} -- {entity['relationship']} -- {entity['destination']}"
        formatted_lines.append(simplified)

    return "\n".join(formatted_lines)


def remove_spaces_from_entities(entity_list):
    for item in entity_list:
        item["source"] = item["source"].lower().replace(" ", "_")
        item["relationship"] = item["relationship"].lower().replace(" ", "_")
        item["destination"] = item["destination"].lower().replace(" ", "_")
    return entity_list


class DeleteGraphMemory(BaseModel):
    """Delete the relationship between two nodes. This function deletes the existing relationship."""

    source: str = Field(..., description="The identifier of the source node in the relationship.")
    relationship: str = Field(..., description="The existing relationship between the source and destination nodes that needs to be deleted.")
    destination: str = Field(..., description="The identifier of the destination node in the relationship.")


def get_delete_entities_from_search_output(search_output, data, user_id):
    """Get the entities to be deleted from the search output."""
    search_output_string = format_entities(search_output)
    system_prompt, user_prompt = get_delete_messages(search_output_string, data, user_id)

    prompt = ChatPromptTemplate.from_messages(
            [
            ("system", system_prompt),
            ("user", "{user_prompt}")
        ]
    )
    structured_llm = search_llm_provider.with_structured_output(DeleteGraphMemory)
    few_shot_structured_llm = prompt | structured_llm
    memory_updates = few_shot_structured_llm.invoke({"user_prompt": user_prompt})
    memory_updates_json = memory_updates.model_dump()
    to_be_deleted = []
    if memory_updates_json:
        to_be_deleted.append(memory_updates_json)   
    # in case if it is not in the correct format
    to_be_deleted = remove_spaces_from_entities(to_be_deleted)
    logger.debug(f"Deleted relationships: {to_be_deleted}")
    return to_be_deleted
