import os
import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Page Config ---
st.set_page_config(page_title="SQL Chatbot", page_icon="🧠", layout="wide")
st.title("🧠 SQL Chatbot with Natural Language using Groq + MySQL")
st.markdown("Ask natural language questions and get SQL queries + results!")

# --- Sidebar for Configuration ---
st.sidebar.header("Database Configuration")

db_user = st.sidebar.text_input("User", "root")
db_password = st.sidebar.text_input("Password", type="password")
db_host = st.sidebar.text_input("Host", "localhost")
db_name = st.sidebar.text_input("Database", "your_database")

groq_api_key = st.sidebar.text_input("Groq API Key", type="password")

if groq_api_key:
    os.environ["GROQ_API_KEY"] = groq_api_key

# --- Create Connection & LLM Only When Inputs Are Ready ---
if groq_api_key and db_user and db_password and db_host and db_name:
    try:
        db_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
        db = SQLDatabase.from_uri(db_uri)

        llm = ChatGroq(temperature=0, model_name="compound-beta-mini")

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a data assistant. Write SQL for this MySQL database:\n{schema}"),
            ("human", "{question}"),
        ])

        sql_chain = prompt | llm | StrOutputParser()
        st.success("✅ Connected to MySQL and LLM!")

        # --- Chat Input ---
        user_question = st.text_input("Ask your question about the database:")
        if user_question:
            try:
                schema = db.get_table_info()
                query = sql_chain.invoke({"question": user_question, "schema": schema})
                st.code(query, language="sql")

                result = db.run(query)
                st.dataframe(result)

            except Exception as e:
                st.error(f"❌ Error: {e}")

    except Exception as db_error:
        st.error(f"Failed to connect to database: {db_error}")
else:
    st.info("⬅️ Please enter your database and API credentials in the sidebar.")
