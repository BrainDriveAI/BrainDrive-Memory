from fastapi import FastAPI, HTTPException
from app.agents.agent_executor import agent_executor as neo4j_semantic_agent
from pydantic import BaseModel

app = FastAPI()


# Model for request data
class SearchRequest(BaseModel):
    search_text: str
    query_type: str


class AddTextRequest(BaseModel):
    text: list


@app.post("/add_text")
def add_text(data: AddTextRequest):
    try:
        print(f"Input add text data: {data}")
        text = data.text

        # Assuming `insert` method of LightRAG
        neo4j_semantic_agent.invoke({"input": text})

        return {"message": "Text added successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search")
def search(data: SearchRequest):
    try:
        search_text = data.search_text
        query_type = data.query_type

        print(f"Search query: {search_text}")

        if query_type not in ["naive", "local", "global", "hybrid", "mix"]:
            raise HTTPException(status_code=400, detail="Invalid query type.")
        
        result = neo4j_semantic_agent.invoke({"input": search_text})

        output = result["output"]

        print(f"Search output: {output}")

        return {"result": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
