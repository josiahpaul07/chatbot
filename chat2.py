import os
import anthropic
import streamlit as st
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate

load_dotenv()
api_key= os.getenv("API_KEY")

template = """Based on the table schema below, write a SQL query without any explanation that would answer the user's question:
{schema}

Question: {question}
SQL Query:
"""
prompt = ChatPromptTemplate.from_template(template)


from langchain_community.utilities import SQLDatabase
sqlite_uri = 'sqlite:///database/mystorep.db'

db = SQLDatabase.from_uri(sqlite_uri)

#db.run("SELECT * FROM Album LIMIT 5")

def get_schema(_):
    return db.get_table_info()
#get_schema(None)

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_anthropic import ChatAnthropic

# Initialize Claude Sonnet with API key
llm = ChatAnthropic(
    model_name="claude-3-5-sonnet-20241022",
    api_key= api_key
)

# Define SQL chain
sql_chain = (
    RunnablePassthrough.assign(schema=get_schema)
    | prompt
    | llm.bind(stop=["\nSQLResult:"])
    | StrOutputParser()
)

#user_question = 'how many albums are there in the database?'
#print(sql_chain.invoke({"question": user_question}))

template = """Based on the table schema below, question, sql query, and sql response, write a natural language response:
{schema}

Question: {question}
SQL Query: {query}
SQL Response: {response}"""
prompt_response = ChatPromptTemplate.from_template(template)

def run_query(query):
    return db.run(query)

full_chain = (
    RunnablePassthrough.assign(query=sql_chain).assign(
        schema=get_schema,
        response=lambda vars: run_query(vars["query"]),
    )
    | prompt_response
    | llm
    | StrOutputParser()
)

#user_question = input("Enter your question: ")
#response = full_chain.invoke({"question": user_question})
#print("\n💡 AI Response:\n" + response)

# Streamlit UI
st.title("Database Query AI")
st.write("Ask a question about this database")

# User Input
user_question = st.text_input("Enter your question:", "")

if st.button("Get Answer"):
    if user_question:
        response = full_chain.invoke({"question": user_question})

        st.subheader("💡 AI Response:")
        st.write(response)

        # Debugging: Show SQL Query
        #sql_query = sql_chain({"question": user_question})
        #st.subheader("📝 Generated SQL Query:")
        #st.code(sql_query, language="sql")

    else:
        st.warning("Please enter a question.")