import streamlit as st
from main import get_data_from_db

st.set_page_config(
    page_title="AskDB",
    page_icon="🕷️",
    layout="centered",
)

st.title("AskDB — AI-Powered Natural Language to SQL")

st.write("Ask questions about your data in natural language.")

user_query = st.text_input("Enter Your question")


if user_query:
    database_response = get_data_from_db(user_query)

    st.success("✅ Analysis Complete!")

    st.write("Here's the analysis for your query:")

    st.markdown(f"**{user_query}**")

    if isinstance(database_response, str):
        st.warning(database_response)

    elif database_response:
        for row in database_response:
            st.write("  ".join(str(value) for value in row))

    else:
        st.info("No results found.")
st.markdown(
    """
            <style>
            textarea{
                font-size: 16px !important;
            }
            </style>
            """,
    unsafe_allow_html=True,
)
