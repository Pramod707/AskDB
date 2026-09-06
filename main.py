# step1:Extract schemas
from sqlalchemy import create_engine, inspect
import json
import re

db_url = "sqlite:///Askdb.db"


def extract_schemas(db_url):
    engine = create_engine(db_url)
    inspector = inspect(engine)
    schema = {}
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        schema[table_name] = [col["name"] for col in columns]
        # print("Table:", table_name, "Columns:", schema[table_name])
    return json.dumps(schema, indent=3)


# step2 : text to sql (using groq model)

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")


def text_to_sql(schema, prompt):
    llm = ChatGroq(model="qwen/qwen3.6-27b", temperature=0)
    SYSTEM_PROMPT = """You are AskDB, an expert Text-to-SQL assistant.


    Your task is to convert a user's natural-language question into a valid SQL query that can be executed against the provided SQLite database.

    Follow these rules strictly:

    1. Use ONLY the tables, columns, and relationships explicitly provided in the database schema.
    2. NEVER invent or assume a table, column, relationship, or value that is not present in the schema.
    3. Generate SQLite-compatible SQL syntax.
    4. Carefully identify the required tables and use JOIN conditions based only on the defined foreign-key relationships.
    5. For aggregation questions, use the appropriate SQL functions such as COUNT, SUM, AVG, MIN, and MAX.
    6. When using aggregation, use GROUP BY correctly.
    7. Use ORDER BY when the user asks for highest, lowest, top, bottom, newest, oldest, etc.
    8. Use LIMIT when the user asks for a specific number of results.
    9. Do not use SELECT * unless the user explicitly asks for all columns. Select only the columns necessary to answer the question.
    10. Do not modify the database.

    Security rules:
    11. NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, REPLACE, ATTACH, DETACH, or other database-modifying statements.
    12. Generate READ-ONLY SELECT queries only.
    13. Never execute SQL yourself. Your responsibility is only to generate the SQL query.

    Accuracy rules:
    14. Read the complete schema before generating the query.
    15. Do not confuse similarly named columns across different tables.
    16. When joining tables, explicitly qualify columns with table names or aliases.
    17. If the user's question cannot be answered using the provided schema, do not invent information. Return:
    "The question cannot be answered using the available database schema."
    18. If the question is ambiguous and different interpretations would produce different SQL queries, ask for clarification instead of guessing.
    19. Make sure every referenced table and column exists in the schema.
    20. Before returning the query, mentally verify the JOIN conditions, filtering, aggregation, grouping, ordering, and LIMIT.

    Output rules:
    21. Return ONLY the SQL query.
    22. Do not include explanations.
    23. Do not use Markdown code fences.
    24. Do not include comments inside the SQL query.

    Database schema:
    {schema}
    """
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", "Question:\n{user_prompt}"),
    ])
    chain = prompt_template | llm
    raw = chain.invoke({"schema": schema, "user_prompt": prompt})
    response = re.sub(r"<think>.*?</think>", "", raw.content, flags=re.DOTALL)
    response = re.sub(r"```sql|```", "", response)

    return response.strip()


schema = extract_schemas(db_url)
prompt = "tell me the names of the customers"

print(text_to_sql(schema, prompt))

# step3 : frontend with streamlit
