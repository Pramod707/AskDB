# step1:Extract schemas
from sqlalchemy import create_engine, inspect
import json
import re
import sqlite3

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
    llm = ChatGroq(model="qwen/qwen3.6-27b", temperature=0, max_tokens=300)
    SYSTEM_PROMPT = """
You are AskDB, an expert SQLite Text-to-SQL assistant.

Convert the user's question into a valid SQLite SELECT query.

Rules:
- Use only tables and columns in the schema.
- Never invent tables, columns, relationships, or values.
- Use valid SQLite syntax.
- Use JOINs only when supported by the schema.
- Use GROUP BY for aggregations when required.
- Use ORDER BY and LIMIT when requested.
- Generate SELECT queries only.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE,
  REPLACE, ATTACH, or DETACH.
- If the question cannot be answered using the schema, return exactly:
  The question cannot be answered using the available database schema.
- Return ONLY the SQL query.
- Do not include explanations or Markdown.

Database schema:
{schema}
"""
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", "Question:\n{user_prompt}"),
    ])
    chain = prompt_template | llm
    raw = chain.invoke({"schema": schema, "user_prompt": prompt})

    response = raw.content

    # Remove Qwen reasoning
    response = re.sub(
        r"<think>.*?</think>", "", response, flags=re.DOTALL | re.IGNORECASE
    )

    # Remove Markdown code fences
    response = re.sub(r"```(?:sql)?", "", response, flags=re.IGNORECASE)

    return response.strip()


# def get_data_from_db(prompt):
#     schema = extract_schemas(db_url)
#     sql_qery = text_to_sql(schema, prompt)
#     conn = sqlite3.connect("Askdb.db")
#     cursor = conn.cursor()
#     cursor.execute(sql_qery)
#     result = cursor.fetchall()
#     conn.close()
#     return result


def get_data_from_db(prompt):
    schema = extract_schemas(db_url)
    sql_qery = text_to_sql(schema, prompt)

    print("GENERATED SQL:", repr(sql_qery))

    if not sql_qery:
        return "No SQL query generated."

    if not sql_qery.strip().lower().startswith("select"):
        return "Invalid SQL query generated."

    conn = sqlite3.connect("Askdb.db")
    cursor = conn.cursor()

    try:
        cursor.execute(sql_qery)
        return cursor.fetchall()

    except sqlite3.Error as e:
        return f"Database error: {e}"

    finally:
        conn.close()


# print(res1)

# step3 : frontend with streamlit
