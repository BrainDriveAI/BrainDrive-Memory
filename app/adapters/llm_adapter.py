from app.app_env import app_env

# OPENAI
from langchain_openai import ChatOpenAI
search_llm_provider = ChatOpenAI(
    temperature=0,
    model=app_env.OPENAI_LLM_MODEL,
    api_key=app_env.OPENAI_API_KEY.get_secret_value(),
    verbose=False,
    streaming=True
)

# OLLAMA
# from langchain_ollama import ChatOllama
# llm_provider = ChatOllama(model="model name")

# OPENROUTER
# llm_provider = ChatOpenAI(temperature=0, model=app_env.OPENROUTER_LLM_MODEL, base_url=str(app_env.OPENROUTER_BASE_URL), api_key=app_env.OPENROUTER_API_KEY.get_secret_value() if app_env.OPENROUTER_API_KEY else None)


# TOGETHER AI
# from langchain_together import ChatTogether
# llm_provider = ChatTogether(
#     together_api_key=togetherai_api_key,
#     model=together_llm_model,
#     api_key=app_env.TOGETHERAI_API_KEY.get_secret_value() if app_env.TOGETHERAI_API_KEY else None,
#     model=app_env.TOGETHER_LLM_MODEL
# )


# GROQ AI
from langchain_groq import ChatGroq
llm_provider = ChatGroq(
    model=app_env.GROQ_LLM_MODEL if app_env.GROQ_LLM_MODEL else "llama3-70b-8192",  # Default if not set
    temperature=0,
    streaming=True,
    api_key=app_env.GROQ_API_KEY.get_secret_value() if app_env.GROQ_API_KEY else None
)
