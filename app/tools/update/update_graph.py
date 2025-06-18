import json
from app.data_source_manager import get_graph_db_instance
from app.adapters.llm_adapter import search_llm_provider
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from typing import Literal

UpdateType = Literal["source", "relationship", "destination"]


def update_graph(update_type: UpdateType, id_value: str, new_value: str, user_id: str):
    """
    Generic method to update nodes or relationships in Neo4j.

    Args:
        update_type (str): "node" or "relationship"
        id_value (str): The ID of the node or relationship to update
        new_value (str): The new value to set
        user_id (str): The user id
    """
    graph_db_service = get_graph_db_instance()
    if update_type == "source":
        query = """
        MATCH (n)
            WHERE elementId(n) = $id_value AND n.user_id = $user_id
        SET
            n.name = $new_value,
            n.updated_at = timestamp()
        RETURN n
        """
    elif update_type == "relationship":
        query = """
        MATCH ()-[r]->()
            WHERE elementId(r) = $id_value
        SET
            r.type = $new_value,
            r.updated_at = timestamp()
        RETURN r
        """
    else:
        raise ValueError("Invalid update_type. Must be 'node' or 'relationship'.")
    
    params = {
        "id_value": id_value,
        "new_value": new_value,
        "user_id": user_id,
    }

    result = graph_db_service.query(query, params=params)
    return result


def format_entities(entities):
    if not entities:
        return ""

    formatted_lines = []
    for entity in entities:
        simplified = json.dumps({
            "source": entity["source"],
            "relationship": entity.get("relationship") or entity.get("relatationship", ""),
            "destination": entity["destination"],
            "source_id": entity["source_id"],
            "relation_id": entity["relation_id"],
            "destination_id": entity["destination_id"],
        }, ensure_ascii=False)  # Keep Unicode characters if needed
        formatted_lines.append(simplified)

    return "\n".join(formatted_lines)


def get_update_messages(existing_memories_string, data, user_id):
    system_prompt = """
        You are an assistant that extracts structured update information from user instructions. 
        Your task is to determine what type of data needs to be updated, the new value
        and the correct entity ID (source_id, relation_id, or destination_id).

        There are three possible update types:
        - "source" → when the user wants to update an entity (e.g., a person, company, or place).
        - "relationship" → when the user wants to update the type of relationship between entities.
        - "destination" → when the user wants to update an entity that is at the receiving end of a relationship.

        Current user's ID: USER_ID

        Your response must be in the following JSON format:
        {{
            "update_type": "<source | relationship | destination>",
            "new_value": "<the new value the user wants>",
            "entity_id": "<the corresponding entity ID>"
        }}

        The entity ID must be selected based on the update type:
        - If "update_type" is "source", use "source_id".
        - If "update_type" is "relationship", use "relation_id".
        - If "update_type" is "destination", use "destination_id".

        Examples:

        **Input:** "Update Chuck's full name as Chuck Roades"
        **Output:**
        {{
            "update_type": "source",
            "new_value": "Chuck Roades",
            "entity_id": "4:c788121e-e836-411f-a0e4-011356079d19:0"
        }}

        **Input:** "Change the relationship between Beck and his nickname to ‘preferred_name’"
        **Output:**
        {{
            "update_type": "relationship",
            "new_value": "preferred_name",
            "entity_id": "5:c788121e-e836-411f-a0e4-011356079d19:1152929201188241408"
        }}

        **Input:** "Change Chuck's nickname to Ben"
        **Output:**
        {{
            "update_type": "destination",
            "new_value": "Ben",
            "entity_id": "4:c788121e-e836-411f-a0e4-011356079d19:1"
        }}
    """.replace("USER_ID", user_id)

    human_message = f"Here are the existing memories: {existing_memories_string} \n\n Latest user request: {data}"

    return system_prompt, human_message


class UpdateGraphMemory(BaseModel):
    """Updates the neo4j knowledge graph database."""

    update_type: UpdateType = Field(..., description="Determine update type. Either: source, relationship, or destination.")
    new_value: str = Field(..., description="The new value to be added.")
    entity_id: str = Field(..., description="The corresponding entity ID")


def process_and_update(search_output, data, user_id):
    """Get the entities to be deleted from the search output."""
    search_output_string = format_entities(search_output)
    system_prompt, user_prompt = get_update_messages(search_output_string, data, user_id)

    prompt = ChatPromptTemplate.from_messages(
            [
            ("system", system_prompt),
            ("user", "{user_prompt}")
        ]
    )
    structured_llm = search_llm_provider.with_structured_output(UpdateGraphMemory)
    few_shot_structured_llm = prompt | structured_llm
    memory_updates = few_shot_structured_llm.invoke({"user_prompt": user_prompt})
    memory_updates_json = memory_updates.model_dump()

    update_type, new_value, entity_id = memory_updates_json.values()

    # Determine what to update
    if update_type == "source":
        update_graph("source", entity_id, new_value, user_id)
    elif update_type == "relationship":
        update_graph("relationship", entity_id, new_value, user_id)
    elif update_type == "destination":
        update_graph("source", entity_id, new_value, user_id)
    return memory_updates_json
