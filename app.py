import streamlit as st
from streamlit_chat import message
from sqlalchemy import create_engine, Column, String, Integer, MetaData, Table, Date, ForeignKey
from sqlalchemy.orm import sessionmaker

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Database connection
DATABASE_URL = "sqlite:///my_database.db"  # Adjust the path as necessary
engine = create_engine(DATABASE_URL)

metadata = MetaData()
metadata.bind = engine

users_table = Table("users", metadata, autoload_with=engine)
reports_table = Table("medical_reports", metadata, autoload_with=engine)


SessionLocal = sessionmaker(bind=engine)

# Check if user exists in the database
def check_user(username, password):
    session = SessionLocal()
    user = session.query(users_table).filter_by(username=username, password=password).first()
    session.close()
    return user

# Fetch reports for a user
def fetch_reports(user_id):
    session = SessionLocal()
    user_reports = session.query(reports_table).filter_by(username=user_id).all()
    session.close()
    return user_reports

def get_response(history,user_message,medical_records,temperature=0):
    print('called')
    DEFAULT_TEMPLATE = """The following is a friendly conversation between a human and a medical expert that has access to all its medical records. 
    The user can ask about his past porcedures. His previous medical reports from the dcotor. He can also ask some clarification about what those symptoms and test means.
    Use your ow knowledge to answer those questions

    Relevant pieces of previous conversation:
    {context},

    All the previous medical records of the user:
    {text}, 

    Current conversation:
    Human: {input}
    Medical Expert:"""

    PROMPT = PromptTemplate(
        input_variables=['context','input','text'], template=DEFAULT_TEMPLATE
    )




  
    chat_gpt = ChatOpenAI(temperature=temperature, model_name="gpt-3.5-turbo")

    conversation_with_summary = LLMChain(
        llm=chat_gpt,
        prompt=PROMPT,
        verbose=False
    )
    response = conversation_with_summary.predict(context=history,input=user_message,text = medical_records)
    return response



# Initialize session state for user login status and conversation history
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

def login_page():
    st.title("Login to Medical Reports App")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = check_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.username = username  # Store the username in the session state
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

def chatbot_page():
    st.title("Chat with Medical Expert")

    reports = fetch_reports(st.session_state.username)
    medical_records = "\n".join([f"Date: {report.date}, Details: {report.report}" for report in reports])

    # Display conversation using the message function
    for i, chat_message in enumerate(st.session_state.conversation_history):
        is_user_message = chat_message['sender'] == 'User'
        message(chat_message['message'], is_user=is_user_message, key=str(i) + ("_user" if is_user_message else ""))

    # Input area for user message
    user_message = st.text_input("Your Message")

    if st.button("Send"):
        # Get chatbot response
        chatbot_response = get_response(st.session_state.conversation_history, user_message, medical_records)

        # Update conversation history
        st.session_state.conversation_history.append({'sender': 'User', 'message': user_message})
        st.session_state.conversation_history.append({'sender': 'Chatbot', 'message': chatbot_response})

        # Refresh the page to display the updated conversation
        st.experimental_rerun()


# Streamlit app
def main():
    if st.session_state.logged_in:
        chatbot_page()
    else:
        login_page()

if __name__ == "__main__":
    main()
