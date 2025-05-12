from app.adapters.llm_adapter import search_llm_provider
from app.logger import app_logger as logger
from pydantic import BaseModel, Field
from typing import List
from langchain_core.prompts import ChatPromptTemplate


class EntityItem(BaseModel):
    """An entity and it's type from the text."""

    entity: str = Field(..., description="The name or identifier of the entity.")
    entity_type: str = Field(..., description="The type or category of the entity.")


class ExtractEntities(BaseModel):
    """Extract entities and their types from the text."""

    entities: List[EntityItem]


def retrieve_nodes_from_data(data, user_id):
    """Extracts all the entities mentioned in the query."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are a smart assistant who understands entities and their types in a given text.
                If user message contains self reference such as 'I', 'me', 'my' etc. then use {user_id} as the source entity.
                Extract all the entities from the text, including persons, organizations, companies, hobbies, likes, relationships and locations. 
                Here are some examples of the entities and their types:
                
                - "beck" is a Person
                - "Apple" is a Company
                - "Microsoft" is a Company
                - "John Doe" is a Person
                - "Google" is an Organization
                - "New York" is a Location
                - "Tesla" is a Company
                - "Tesla's" is a company (when referring to something owned by Tesla)
                
                Make sure to capture organizations or companies, even if they are referred to indirectly or implicitly (e.g., 'my company', 'my business', 'I work at Tesla', etc.).
                ***DO NOT*** answer the question itself if the given text is a question.""",
            ),
            ("user", "{user_input}"),
        ]
    )

    structured_llm = search_llm_provider.with_structured_output(ExtractEntities)
    few_shot_structured_llm = prompt | structured_llm
    search_results = few_shot_structured_llm.invoke({"user_input": data})

    search_results_json = search_results.model_dump()

    print(f"input data: {data}")

    print(f"Entities retrieved results: {search_results_json}")

    entity_type_map = {}

    try:
        for item in search_results_json["entities"]:
            entity_type_map[item["entity"]] = item["entity_type"]
    except Exception as e:
        logger.error(f"Error in search tool: {e}")

    entity_type_map = {k.lower().replace(" ", "_"): v.lower().replace(" ", "_") for k, v in entity_type_map.items()}
    logger.debug(f"Entity type map: {entity_type_map}")
    return entity_type_map
