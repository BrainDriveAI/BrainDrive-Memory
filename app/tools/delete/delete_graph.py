import json
from app.data_source_manager import get_graph_db_instance
from app.adapters.llm_adapter import search_llm_provider
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from typing import Literal


DeleteType = Literal["source", "relationship"]


def delete_from_graph(delete_type: DeleteType, id_value: str, user_id: str):
    """
    Generic method to delete nodes or relationships in Neo4j.

    Args:
        delete_type (str): "source" (node) or "relationship"
        id_value (str): The ID of the node or relationship to delete
        user_id (str): The ID of the user to delete
    """
    graph_db_service = get_graph_db_instance()
    if delete_type == "source":
        query = """
        MATCH (n)
        WHERE elementId(n) = $id_value AND n.user_id = $user_id
        DETACH DELETE n
        RETURN COUNT(n) AS deleted_count
        """
    elif delete_type == "relationship":
        query = """
        MATCH ()-[r]->()
        WHERE elementId(r) = $id_value
        DELETE r
        RETURN COUNT(r) AS deleted_count
        """
    else:
        raise ValueError("Invalid delete_type. Must be 'source' or 'relationship'.")
    
    params = {
        "id_value": id_value,
        "user_id": user_id,
    }

    result = graph_db_service.query(query, params=params)
    print(f"PERFORMED DELETE ACTION. Delete type: {delete_type}. Delete id: {id_value}. Delete result: {result}")
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


def get_delete_prompts(existing_memories_string, data, user_id):
    system_prompt = """
        You are an assistant that extracts structured delete information from user instructions.
        Your task is to determine what type of data needs to be deleted and the correct entity ID 
        (source_id or relation_id).

        There are two possible delete types:
        - "source" → when the user wants to delete an entity (e.g., a person, company, or place).
        - "relationship" → when the user wants to delete a connection between two entities.

        Current user's ID: USER_ID

        Your response must be in the following JSON format:
        {{
            "delete_type": "<source | relationship>",
            "entity_id": "<the corresponding entity ID>"
        }}

        The entity ID must be selected based on the delete type:
        - If "delete_type" is "source", use "source_id".
        - If "delete_type" is "relationship", use "relation_id".

        Examples:

        **Input:** "Delete Beck from memory"
        **Output:**
        {{
            "delete_type": "source",
            "entity_id": "4:c788121e-e836-411f-a0e4-011356079d19:0"
        }}

        **Input:** "Remove the nickname relationship between Beck and Ben"
        **Output:**
        {{
            "delete_type": "relationship",
            "entity_id": "5:c788121e-e836-411f-a0e4-011356079d19:1152929201188241408"
        }}
    """.replace("USER_ID", user_id)

    human_message = f"Here are the existing memories: {existing_memories_string} \n\n Latest user request: {data}"

    return system_prompt, human_message


class DeleteGraphMemory(BaseModel):
    """Deletes the Neo4j knowledge graph database."""

    delete_type: DeleteType = Field(..., description="Determine delete type. Either: source or relationship.")
    entity_id: str = Field(..., description="The corresponding entity ID")


def process_and_delete(search_output, data, user_id):
    """Get the entities to be deleted from the search output."""
    search_output_string = format_entities(search_output)
    system_prompt, user_prompt = get_delete_prompts(search_output_string, data, user_id)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{user_prompt}")
        ]
    )

    structured_llm = search_llm_provider.with_structured_output(DeleteGraphMemory)
    few_shot_structured_llm = prompt | structured_llm
    delete_decision = few_shot_structured_llm.invoke({"user_prompt": user_prompt})
    delete_decision_json = delete_decision.model_dump()

    delete_type, entity_id = delete_decision_json.values()

    # Perform the delete action
    delete_from_graph(delete_type, entity_id, user_id)

    return delete_decision_json
