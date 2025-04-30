import os
import sqlite3
import tempfile

import streamlit as st
from langchain.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

# --- Page Setup ---
st.set_page_config(page_title="SQL Chatbot", page_icon="🧠", layout="wide")
st.title("🧠 SQL Chatbot from MySQL File using Groq")
st.markdown("Upload your `.sql` file to query it with natural language using Groq LLM!")

# --- Sidebar Inputs ---
st.sidebar.header("LLM Configuration")
groq_api_key = st.sidebar.text_input("Groq API Key", type="password")

# --- File Uploader ---
uploaded_file = st.file_uploader("Upload your MySQL .sql file", type=["sql"])

# --- Main Logic ---
if groq_api_key:
    os.environ["GROQ_API_KEY"] = groq_api_key

    if uploaded_file:
        try:
            # Save uploaded SQL file to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp_file:
                db_path = tmp_file.name

            # Create SQLite DB and execute uploaded SQL
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            sql_script = uploaded_file.read().decode("utf-8")
            cursor.executescript(sql_script)
            conn.commit()
            conn.close()

            # Create LangChain DB interface
            db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
            llm = ChatGroq(temperature=0, model_name="compound-beta-mini")  # or compound-beta-mini
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a data assistant. Write SQL for this database:\n{schema}"),
                ("human", "{question}"),
            ])
            sql_chain = prompt | llm | StrOutputParser()

            st.success("✅ Database loaded and LLM is ready!")

            # --- User Chat Input ---
            user_question = st.text_input("Ask a question about your data:")
            if user_question:
                try:
                    schema = db.get_table_info()
                    query = sql_chain.invoke({"question": user_question, "schema": schema})
                    st.code(query, language="sql")
                    result = db.run(query)
                    st.dataframe(result)

                except Exception as e:
                    st.error(f"❌ Query Error: {e}")

        except Exception as e:
            st.error(f"❌ Failed to process SQL file: {e}")

else:
    st.info("⬅ Please upload a `.sql` file and enter your Groq API key to continue.")
