# main.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from langchain_google_vertexai import ChatVertexAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.agents import create_sql_agent

# --- Configuration ---
# These environment variables will be set by Cloud Run during deployment,
# pulling values from Secret Manager.
PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("GCP_REGION")
DB_USER = os.environ.get("db_user")
DB_PASS = os.environ.get("db_password")
DB_NAME = "providers" # The database you created in Cloud SQL
INSTANCE_CONNECTION_NAME = os.environ.get("db_instance_connection_name")


# --- Initialization ---
# Initialize the Vertex AI LLM
# Using a powerful model is key for reliable Text-to-SQL
llm = ChatVertexAI(
    project=PROJECT_ID,
    location=REGION,
    model_name="gemini-1.5-pro-latest",
    temperature=0.0  # Set to 0 for deterministic, factual SQL generation
)

# Construct the database URI for connecting via the Cloud SQL Auth Proxy
db_uri = (
    f"postgresql+pg8000://{DB_USER}:{DB_PASS}@/{DB_NAME}"
    f"?unix_sock=/cloudsql/{INSTANCE_CONNECTION_NAME}/.s.PGSQL.5432"
)

# Initialize the LangChain SQLDatabase wrapper
db = SQLDatabase.from_uri(db_uri)

# Create the LangChain SQL Agent
# This agent has the tools to interact with the database.
agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="openai-tools", # This agent style works well with Gemini's function calling
    verbose=True # Set to True for detailed logging of the agent's thoughts and SQL queries
)


# --- API Definition ---
app = FastAPI(
    title="ProviderFlow AI API",
    description="An API to query Northwell Health provider data using natural language."
)

class QueryRequest(BaseModel):
    """The request model for the /query endpoint."""
    question: str

@app.get("/", summary="Health Check")
def read_root():
    """A simple health check endpoint to confirm the API is running."""
    return {"status": "ProviderFlow AI API is running"}

@app.post("/query", summary="Query the Provider Database")
async def query_agent(request: QueryRequest):
    """
    Receives a natural language question, passes it to the SQL agent,
    and returns the agent's final answer.
    """
    try:
        # Use 'ainvoke' for asynchronous execution, which works well with FastAPI
        response = await agent_executor.ainvoke({"input": request.question})
        return {"question": request.question, "answer": response["output"]}
    except Exception as e:
        # Log the full error for debugging on the backend
        print(f"Error processing query: {e}")
        # Return a user-friendly error message
        raise HTTPException(
            status_code=500,
            detail="The AI agent failed to process the query. Please try rephrasing your question."
        )