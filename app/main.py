import streamlit as st
from faq import ingest_faq_data, faq_chain
from sql import sql_chain
from pathlib import Path
from router import router

faqs_path = Path(__file__).parent / "resources/faq_data.csv"
ingest_faq_data(faqs_path)


def ask(query):
    route = router(query).name
    if route == 'faq':
        return faq_chain(query)
    elif route == 'sql':
        return sql_chain(query)
    else:
        return f"Route {route} not implemented yet"

st.title("E-commerce Bot")
st.subheader("👋 Hi there! I’m your E-commerce Assistant")
st.markdown("""
### 🔍 Suggested Queries  
Try one of these to get started. 

#### 🛒 Product Search
- **"Puma running shoes under ₹3000"**  
- **"Nike shoes with rating above 4.2"**   
- **"Formal black shoes below ₹2500"**  

#### 💬 FAQs
- **"What payment methods do you accept?"**  
- **"How long does refund take?"**  
- **"Do you offer cash on delivery?"**

You can also ask your own question!
⚠️ Tiny heads-up: Super broad product searches can sometimes overwhelm our baby bot.
We're still early stage, thanks for being gentle with it! 😄
""")


query = st.chat_input("Write your query")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if query:
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role":"user", "content":query})

    response = ask(query)
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})


