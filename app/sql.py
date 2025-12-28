from groq import Groq
import os
import re
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# -------------------------------
# CONSTANTS
# -------------------------------
GROQ_MODEL = os.getenv("GROQ_MODEL")
client_sql = Groq()

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "db.sqlite"
CSV_PATH = BASE_DIR / "resources" / "ecommerce_data_final.csv"


# -------------------------------
# AUTO-INITIALIZE DB IF MISSING
# -------------------------------
def init_db():
    """Creates SQLite DB + product table if missing on Streamlit."""
    if DB_PATH.exists():
        return  # DB already exists

    df = pd.read_csv(CSV_PATH)

    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("product", conn, if_exists="replace", index=False)


init_db()  # ensure DB exists on deploy


# -------------------------------
# PROMPTS
# -------------------------------
sql_prompt = """You are an expert in understanding the database schema and generating SQL queries for a natural language question asked
pertaining to the data you have. The schema is provided in the schema tags. 
<schema> 
table: product 

fields: 
product_link - string (hyperlink to product)	
title - string (name of the product)	
brand - string (brand of the product)	
price - integer (price of the product in Indian Rupees)	
discount - float (discount on the product. 10 percent discount is represented as 0.1, 20 percent as 0.2)	
avg_rating - float (average rating of the product. Range 0-5)	
total_ratings - integer (total number of ratings)
</schema>

Rules:
- Always return SELECT * queries only.
- Use LIKE %...% for brand matching. Never use ILIKE.
- Return only SQL inside <SQL></SQL> tags.
"""

comprehension_prompt = """You will receive Question: and Data:. Respond ONLY based on data.
When returning multiple products, format like:
1. Title: Rs. PRICE (X percent off), Rating: AVG_RATING <link>
"""


# -------------------------------
# SQL GENERATION
# -------------------------------
def generate_sql_query(question: str) -> str:
    completion = client_sql.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": sql_prompt},
            {"role": "user", "content": question}
        ],
    )
    return completion.choices[0].message.content


# -------------------------------
# EXECUTE SQL
# -------------------------------
def run_query(query: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(query, conn)
            return df
    except Exception as e:
        return None


# -------------------------------
# COMPREHENSION
# -------------------------------
def data_comprehension(question: str, context):
    completion = client_sql.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": comprehension_prompt},
            {"role": "user", "content": f"QUESTION: {question}. DATA: {context}"}
        ],
    )
    return completion.choices[0].message.content


# -------------------------------
# MAIN CHAIN
# -------------------------------
def sql_chain(question: str):
    llm_output = generate_sql_query(question)

    sql_matches = re.findall(r"<SQL>(.*?)</SQL>", llm_output, re.DOTALL)

    if not sql_matches:
        return "Sorry, could not generate SQL for your query."

    sql_query = sql_matches[0].strip()

    df = run_query(sql_query)
    if df is None or df.empty:
        return "No matching products found for your query."

    context = df.to_dict(orient="records")

    return data_comprehension(question, context)


# -------------------------------
# RUN LOCALLY FOR TESTING
# -------------------------------
if __name__ == "__main__":
    q = "Show top 3 shoes in descending order of rating"
    print(sql_chain(q))





















# from groq import Groq
# import os
# import re
# import sqlite3
# import pandas as pd
# from pathlib import Path
# from dotenv import load_dotenv
# from pandas import DataFrame
#
# load_dotenv()
#
# GROQ_MODEL = os.getenv('GROQ_MODEL')
#
# db_path = Path(__file__).parent / "db.sqlite"
#
# client_sql = Groq()
#
# sql_prompt = """You are an expert in understanding the database schema and generating SQL queries for a natural language question asked
# pertaining to the data you have. The schema is provided in the schema tags.
# <schema>
# table: product
#
# fields:
# product_link - string (hyperlink to product)
# title - string (name of the product)
# brand - string (brand of the product)
# price - integer (price of the product in Indian Rupees)
# discount - float (discount on the product. 10 percent discount is represented as 0.1, 20 percent as 0.2, and such.)
# avg_rating - float (average rating of the product. Range 0-5, 5 is the highest.)
# total_ratings - integer (total number of ratings for the product)
#
# </schema>
# Make sure whenever you try to search for the brand name, the name can be in any case.
# So, make sure to use %LIKE% to find the brand in condition. Never use "ILIKE".
# Create a single SQL query for the question provided.
# The query should have all the fields in SELECT clause (i.e. SELECT *)
#
# Just the SQL query is needed, nothing more. Always provide the SQL in between the <SQL></SQL> tags."""
#
#
# comprehension_prompt = """You are an expert in understanding the context of the question and replying based on the data pertaining to the question provided. You will be provided with Question: and Data:. The data will be in the form of an array or a dataframe or dict. Reply based on only the data provided as Data for answering the question asked as Question. Do not write anything like 'Based on the data' or any other technical words. Just a plain simple natural language response.
# The Data would always be in context to the question asked. For example is the question is “What is the average rating?” and data is “4.3”, then answer should be “The average rating for the product is 4.3”. So make sure the response is curated with the question and data. Make sure to note the column names to have some context, if needed, for your response.
# There can also be cases where you are given an entire dataframe in the Data: field. Always remember that the data field contains the answer of the question asked. All you need to do is to always reply in the following format when asked about a product:
# Produt title, price in indian rupees, discount, and rating, and then product link. Take care that all the products are listed in list format, one line after the other. Not as a paragraph.
# For example:
# 1. Campus Women Running Shoes: Rs. 1104 (35 percent off), Rating: 4.4 <link>
# 2. Campus Women Running Shoes: Rs. 1104 (35 percent off), Rating: 4.4 <link>
# 3. Campus Women Running Shoes: Rs. 1104 (35 percent off), Rating: 4.4 <link>
#
# """
#
#
# def generate_sql_query(question):
#     chat_completion = client_sql.chat.completions.create(
#         messages=[
#             {
#                 "role": "system",
#                 "content": sql_prompt,
#             },
#             {
#                 "role": "user",
#                 "content": question,
#             }
#         ],
#         model=os.environ['GROQ_MODEL'],
#         temperature=0.2,
#         max_tokens=1024
#     )
#
#     return chat_completion.choices[0].message.content
#
#
#
# def run_query(query):
#     if query.strip().upper().startswith('SELECT'):
#         with sqlite3.connect(db_path) as conn:
#             df = pd.read_sql_query(query, conn)
#             return df
#
#
# def data_comprehension(question, context):
#     chat_completion = client_sql.chat.completions.create(
#         messages=[
#             {
#                 "role": "system",
#                 "content": comprehension_prompt,
#             },
#             {
#                 "role": "user",
#                 "content": f"QUESTION: {question}. DATA: {context}",
#             }
#         ],
#         model=os.environ['GROQ_MODEL'],
#         temperature=0.2,
#         # max_tokens=1024
#     )
#
#     return chat_completion.choices[0].message.content
#
#
#
# def sql_chain(question):
#     sql_query = generate_sql_query(question)
#     pattern = "<SQL>(.*?)</SQL>"
#     matches = re.findall(pattern, sql_query, re.DOTALL)
#
#     if len(matches) == 0:
#         return "Sorry, LLM is not able to generate a query for your question"
#
#     print(matches[0].strip())
#
#     response = run_query(matches[0].strip())
#     if response is None:
#         return "Sorry, there was a problem executing SQL query"
#
#     context = response.to_dict(orient='records')
#
#     answer = data_comprehension(question, context)
#     return answer
#
#
# if __name__ == "__main__":
#     # question = "All shoes with rating higher than 4.5 and total number of reviews greater than 500"
#     # sql_query = generate_sql_query(question)
#     # print(sql_query)
#     question = "Show top 3 shoes in descending order of rating"
#     # question = "Show me 3 running shoes for woman"
#     # question = "sfsdfsddsfsf"
#     answer = sql_chain(question)
#     print(answer)
