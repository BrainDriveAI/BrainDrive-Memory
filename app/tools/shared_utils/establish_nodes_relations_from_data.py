from app.adapters.llm_adapter import search_llm_provider
from app.logger import app_logger as logger
from pydantic import BaseModel, Field
from typing import List
from app.tools.shared_utils.prompts import EXTRACT_RELATIONS_PROMPT
from langchain_core.prompts import ChatPromptTemplate


class EntityItem(BaseModel):
    """A source entity, relationship and destination entity from the text."""

    source_entity: str = Field(..., description="The source entity of the relationship.")
    relationship: str = Field(..., description="The relationship between the source and destination entities.")
    destination_entity: str = Field(..., description="The destination entity of the relationship.")


class EstablishRelations(BaseModel):
    """Establish relationships among the entities based on the provided text."""

    entities: List[EntityItem]


def _remove_spaces_from_entities(entity_list):
    for item in entity_list:
        item["source"] = item["source_entity"].lower().replace(" ", "_")
        item["relationship"] = item["relationship"].lower().replace(" ", "_")
        item["destination"] = item["destination_entity"].lower().replace(" ", "_")
    return entity_list


def establish_nodes_relations_from_data(data, user_id, entity_type_map):
    """Establish relations among the extracted nodes."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                EXTRACT_RELATIONS_PROMPT.replace("USER_ID", user_id),
            ),
            ("user", "List of entities: {entries_list}. \n\nText: {data}"),
        ]
    )

    structured_llm = search_llm_provider.with_structured_output(EstablishRelations)
    few_shot_structured_llm = prompt | structured_llm
    extracted_entities_response = few_shot_structured_llm.invoke({"entries_list": list(entity_type_map.keys()), "data": data})

    extracted_entities_json = extracted_entities_response.model_dump()

    if extracted_entities_json["entities"]:
        extracted_entities = extracted_entities_json["entities"]
    else:
        extracted_entities = []

    print(f"extracted entities: {extracted_entities}")

    extracted_entities = _remove_spaces_from_entities(extracted_entities)
    logger.debug(f"Extracted entities: {extracted_entities}")
    return extracted_entities

