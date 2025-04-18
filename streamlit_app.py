import streamlit as st
import time
import pandas as pd
import re
from snowflake.snowpark.context import get_active_session
import snowflake.connector

# Set up page configuration
st.set_page_config(layout="wide")

# Get the current Snowflake session
session = get_active_session()

# Function to fetch data from the Snowflake table
def get_data():
    df = session.table("supplier_info") 
    return df

def reset_session_state():
    st.session_state.messages = []
    st.session_state.previous_results = [] 
    st.rerun()

# Function to check if a SQL query is valid
def test_sql(query):
    try:
        query = query.replace('"', "'")
        result = session.sql("select * from supplier_data.public.supplier_info where " + query + " limit 1").collect()  
        return True
    except Exception as e:
        return False

# Format output for displaying
def format_output(s):
    formatted_output = re.sub(r'<q1>(.+)</q1>', r'<q1>:green[\1]</q1>', s)
    formatted_output = re.sub(r'<q2>(.+)</q2>', r'<q2>:green[\1]</q2>', formatted_output)
    formatted_output = formatted_output.replace("</q1>", "</q1>  \n")
    ret_phrase = "Here's my answer "
    return ret_phrase

st.markdown("""
    <style>
        /* Title and message style */
        h1 {
            color: #FFD700;  /* Softer yellow (golden) */
            font-family: 'Courier New', monospace;
            white-space: nowrap; /* Prevent wrapping */
            overflow: hidden;   /* Hide the overflow to maintain the typing effect */
            display: inline-block; /* Ensure it stays on the same line */
            animation: typing 3s steps(40) 1s 1 normal both;
        }
        @keyframes typing {
            from {
                width: 0;
            }
            to {
                width: 100%;
            }
        }

        /* Sidebar button style */
        .stButton>button {
            background-color: #FFD700;  /* Softer yellow (golden) */
            color: black;
            font-weight: bold;
        }

        /* Chat message style */
        .stMarkdown {
            color: white;  /* Softer yellow (golden) */
        }

        /* Typewriter effect for message beneath the title */
        .typewriter-message {
            font-size: 20px;
            color: white;  /* Softer yellow (golden) */
            font-family: 'Courier New', monospace;
            white-space: nowrap;
            overflow: hidden;
            display: inline-block;
            animation: typing 3s steps(40) 1s 1 normal both;
        }

        .chat-message {
            margin-top: 20px;
            font-size: 16px;
            padding: 10px;
            border-radius: 10px;
            background-color: #2b2b2b;  /* Dark background for chat */
            color: white;
        }

        .user-message {
            background-color: #3c3c3c;  /* Slightly lighter dark gray */
            text-align: left;
        }

        .assistant-message {
            background-color: transparent;  /* Slightly lighter dark gray */
            text-align: right;
        }

    </style>
""", unsafe_allow_html=True)


# Set title with typewriter effect
st.title("Smart Procure🔎")

# Message beneath title with typewriter effect

# chnage color and content, add logo to title
st.markdown("""
    <p class="typewriter-message">
        Welcome to Smart Procure! Type your questions below to interact with your data.
    </p>
""", unsafe_allow_html=True)
prompt1 = """
select snowflake.cortex.complete('llama2-70b-chat', '<Context>You are a chatbot for supplier search. Based on the user query, you need to determine if they are asking for a supplier list or just chatting. If the user is searching for suppliers, then do this:The question can be separated by comma,and,or. 
You need decompose the question into 2 parts. You always have to return the parts within the tags. 
If the same questions is asked by the user as given in the examples here then do the query decomposition as given in the output of the same example question.
- Part 1 (SQL): A WHERE clause using the available columns: SUPPLIER_NAME, SKU_NAME, CATEGORY, MANUFACTURING_TYPE, PREV_YEAR_PRICE, CURR_YEAR_PRICE, YOY_PRICE, GEO, LOCATION, MINIMUM_ORDER_QUANTITY, PAYMENT_TERMS,
WARRANTY_IN_YEARS, LEAD_TIME_IN_DAYS, YEAR_OVER_YEAR_PRICE_INCREASE_PERCENTAGE, YEAR_OVER_YEAR_COST_SAVINGS_PERCENTAGE, CERTIFICATION, NO_OF_LATE_SHIPMENTS, SHIPMENT_DELAY_IN_DAYS, NO_OF_SCAR_ISSUED, NO_OF_OPEN_SCAR, NO_OF_CLOSED_SCAR, 
INNOVATION_SCORE, RESPONSIVENESS_SCORE, SERVICE_SCORE, FLEXIBILITY_SCORE, INDUSTRY_EXPERIENCE_SCORE, FINANCIAL_STABILITY_SCORE, PROCESS_EFFICIENCY_SCORE, SUSTAINABILITY_SCORE, ENVIRONMENT_COMPLIANCE_SCORE, TRADE_COMPLIANCE_SCORE, LISTED_CERTIFICATIONS,
NO_OF_PO_ISSUED_PREVIOUS_YEAR, OVERALL_PO_VALUE_PREVIOUS_YEAR, NO_OF_PO_ISSUE_CURRENT_YEAR, OVERALL_PO_VALUE_CURRENT_YEAR, DISASTER_RECOVERY_SCORE, SUPPLIER_NETWORK_SCORE, GEOGRAPHIC_RISK, POLITICAL_RISK, AVG_SHIPMENT_DELAY_IN_DAYS, REGULATORY_SCORE,
YOY_PO_VALUE_GROWTH_PERCENTAGE, SUPPLIER_SCORE, SUSTAINABILITY_PRACTICES, CUSTOMER_FEEDBACK, Production_Capacity_Units_Per_Month, Innovation_Reports, Technical_Descriptions, Patent_Information, Supplier_Capabilities, Supplier_Performance_Reviews, RnD_Achievements, 
Case_Studies, Pricing_Strategies, Production_Process_Details, Operational_Strategies, Past_Quotations.  You always have to return the parts within the tags. The filters for the sql portion should reside inside the tages <q1> and </q1>.
- Part 2 (Text): A natural language interpretation of the query. The content for part 2 should reside within the tags <q2> and </q2>. Do not provide repeated or overlapping criteria in each part.

Example 1: Question: Can you show suppliers based in the USA who offer instruments and provide a warranty of at least 4 years?. Output: <q1>GEO = "USA" AND CATEGORY = "Instruments" and WARRANTY_IN_YEARS >= 4</q1> <q2></q2>

Example 2: Question: Top suppliers in the Equipment category with a lead time of less than 30 days. Output: <q1>CATEGORY = "Equipment" AND LEAD_TIME_IN_DAYS < 30</q1> <q2>suppliers in the Equipment category with a lead time of less than 30 days</q2>

Example 3: Question: Show me suppliers with high innovation scores and good responsiveness. Output: <q1>INNOVATION_SCORE > 7 AND RESPONSIVENESS_SCORE > 8</q1> <q2>suppliers with high innovation and responsiveness scores</q2>

Example 4: Question: Provide a list of suppliers in India who offer equipment and have no open SCAR: <q1>Geo="India" and CATEGORY = "Equipment" and NO_OF_OPEN_SCAR = 0</q1> <q2>suppliers in india who offer equipment but no open scar</q2>

Example 5: Question: Suppliers who are FDA approved as well as ISO certified in US region in consumables category  Output: <q1>GEO = "USA" and CATEGORY = "Equipment" and (certification like "%FDA%" and certification like "%ISO%")  </q1> <q2>suppliers with ISO or FDA certified for consumables in the USA</q2>

Example 6: Question: Who are the Top Green Suppliers in the USA for Equipments?: <q1>GEO = "USA" and CATEGORY = "Equipment" <q2>suppliers who follow green manufacturing practices or Sustainable or renewable or Environment friendly or has ESG or has Certifications like ISO 14001 or Energy star</q2>

Example 7: Question: Show me suppliers in India with volumne-based discount Output: <q1>Geo="India"</q1> <q2>suppliers with volume-based discount</q2>

Example 8: Question: suppliers who implement environmentally friendly
injection practices, particularly focusing on reducing carbon emissions?  Output: <q1></q1> <q2>suppliers who follow green manufacturing practices or Sustainable or renewable or Environment friendly or has ESG or has Certifications like ISO 14001 or Energy star</q2>

Example 9: Question: List Ultrasound Scanner Suppliers who have less than 8 days of lead time and least number of late shipments? Output: <q1>SKU_NAME = "Ultrasound Scanner" and LEAD_TIME_IN_DAYS<=8 AND NO_OF_LATE_SHIPMENTS < 10</q1> <q2>ultrasound scanners suppliers with less than 10 late shipments and less than or equal to 8 lead time in days</q2>

Example 10: Question: Show Supplier which provides product injector tip with high precision molding Output: <q1></q1> <q2>suppliers who have the product injector tip with high precision molding</q2>

Example 11: Question: List of suppliers offering precision injection molding services in the Manchester area, with warranties longer than two years.  Output: <q1>LOCATION ="Manchester" and MANUFACTURING_TYPE = "Injection Molding" and WARRANTY_IN_YEARS > 2</q1> <q2>Suppliers offering precision injection molding services in the Manchester with warranties longer than two years</q2>

Example 12: Question: Suppliers who implement injection molding practices using Biodegradable products <q1>MANUFACTURING_TYPE ="Injection Molding" and lower(supplier_overview) like "%biodegradable%"</q1> <q2>suppliers with injestion molding practices using biodegradable products</q2>

Example 13: Question: List of suppliers in USA with Energy-efficient production <q1>GEO="USA" and SUSTAINABILITY_PRACTICES like "%Energy-efficient production%" or SUSTAINABILITY_PRACTICES like "%Energy efficient%"</q1><q2></q2>

Example 14: Question: Who are the top suppliers with sustainable practices for injection molding in North America?<q1>GEO = "North America" AND MANUFACTURING_TYPE = "Injection Molding" AND SUSTAINABILITY_SCORE > 7</q1><q2></q2>

Example 15: Question: Which suppliers have the shortest Minimum Order Quantity (MOQ) for injection molding<q1>MANUFACTURING_TYPE = "Injection Molding" and MINIMUM_ORDER_QUANTITY<=100</q1><q2></q2>

Example 16: Question: Find suppliers in the USA with FDA-certified injection molding facilities or other accessories for medical devices?<q1>GEO = "USA" and MANUFACTURING_TYPE = "Injection Molding" and CERTIFICATION like "%FDA%" and CATEGORY = "Accessories"</q1><q2></q2>

If the questions is the same as the given examples above then use the content given in the <q1> and <q2> tags. You MUST return the parts inside the tags.You should not repeat the same criteria in both parts. If no clear conditions are found, provide only the natural language interpretation. If the SQL query (Part 1) contains sufficient and clear conditions to identify the suppliers based on the users question, then leave Part 2 (the natural language interpretation) blank.

</Context> <Question>{}</Question> ')
"""

prompt2 = " The output format is : \
\
Part 1: 1 if all criteria are met, and 0 otherwise \
\
Part 2: Provide explanation \
\
\
Example Output: \
Part 1: 1 \
Part 2: {Explain} \
\
Do not provide any other explanation outside of this format\
')"

# Sidebar with a reset button
with st.sidebar:
    st.divider()
    _, btn_container, _ = st.columns([2, 6, 2])
    if btn_container.button("Clear Chat History", use_container_width=True):
        reset_session_state()
    st.sidebar.empty()

    # Add the logo at the bottom of the sidebar
    # Add custom CSS for padding
    st.markdown("<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

    st.image('https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTeJwCIMdKOMZWvzg4SPYG9o1wBFu6GwcQseA&s', width = 275)

st.chat_message("user").markdown("What Questions can I ask?")
st.chat_message("Assistant").markdown("This data model contains information about suppliers, products, and their associated data such as Location, Quotation, a brief overview and more. You can ask questions about the suppliers and their details to gain insights.")


# adding buttons in ui

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "previous_results" not in st.session_state:
    st.session_state.previous_results = []

# Display existing messages in the chat
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):  # Display message as a chat bubble
        if message["role"] == "assistant":
            # Format assistant's message for better readability
            st.markdown(format_output(message["content"]))
        else:
            # Directly display the user message as plain text
            st.markdown(message["content"])

# Display previous results from the previous queries
for previous_df in st.session_state.previous_results:
    if previous_df is not None and not previous_df.empty:
        # Convert DataFrame to HTML and apply custom styles
        df_html = previous_df.to_html(classes="styled-table", escape=False)  # Convert DataFrame to HTML
        st.markdown(
            """
            <style>
                .styled-table {
                    border: 2px solid yellow; /* Border around the entire table */
                    border-radius: 10px;       /* Rounded corners */
                    padding: 10px;
                    width: 100%;
                    box-sizing: border-box;
                }
                .styled-table th, .styled-table td {
                    border: none;  /* Remove borders between cells */
                    padding: 8px;
                    text-align: left;
                }
            </style>
            """, 
            unsafe_allow_html=True
        )
        st.markdown(df_html, unsafe_allow_html=True)

# Handle user input
if prompt:= st.chat_input():
    prompt = prompt.replace("'", r"\'")  # Escape single quotes to prevent errors

    # Step 1: Display the user message (question) immediately
    st.session_state.messages.append({"role": "user", "content": prompt})  # Add user message
    st.chat_message("user").markdown(prompt)  # Show user question in chat bubble

    # Step 2: Add spinner while the assistant processes the response
    with st.spinner('Processing your request...'):
        time.sleep(2)  # Simulating processing time
        prompt1_formatted = prompt1.format(st.session_state.messages[-1]["content"])  # Prepare the prompt for Snowflake SQL
        decomposed = session.sql(prompt1_formatted).collect()[0][0]  # Get the decomposed response

    # Step 3: Parse the decomposed response into SQL (q1) and text (q2) components
    q1_phrase = ""
    q2_phrase = ""
    q1_search = re.search('<q1>(.+)</q1>', decomposed, re.IGNORECASE)
    if q1_search:
        q1_phrase = q1_search.group(1).strip()
        
    q2_search = re.search('<q2>(.+)</q2>', decomposed, re.IGNORECASE)
    if q2_search:
        q2_phrase = q2_search.group(1).strip()

    # Step 4: Validate and construct SQL query
    if not test_sql(q1_phrase):
        q1_phrase = ""  # If the SQL is invalid, reset q1_phrase

    # Construct the final query based on q1_phrase and q2_phrase
    query = ""
    if q1_phrase != "" and q2_phrase != "":
        q1embed = "select *,VECTOR_L2_DISTANCE(supplier_overview_embedding, snowflake.cortex.embed_text_768('e5-base-v2', '{llm}')) from supplier_data.public.supplier_info \
                  where {where} order by SUPPLIER_SCORE asc limit 10"
        q1 = q1embed.format(llm=q2_phrase, where=q1_phrase.replace('"', "'"))
        q2 = "select SUPPLIER_NAME, SKU_NAME, CATEGORY,GEO, LOCATION, MANUFACTURING_TYPE, SUPPLIER_SCORE, WARRANTY_IN_YEARS, CERTIFICATION, CURR_YEAR_PRICE,  MINIMUM_ORDER_QUANTITY from "
        query = q2 + "(" + q1 + ")"
    else:
        query = ""

    # Step 5: Display the assistant's response
    st.session_state.messages.append({"role": "assistant", "content": decomposed})  # Add assistant response to session state
    st.chat_message("assistant").markdown("Here's my Answer")  # Display assistant response in chat bubble

    # Step 6: Execute the query and show the DataFrame (if available)
    if query:
        df = session.sql(query).to_pandas()
    
        # Display DataFrame if it exists
        if not df.empty:
            # Convert DataFrame to HTML
            df_html = df.to_html(classes="styled-table", escape=False)  # Convert DataFrame to HTML
            
            # Modify the HTML to make 'supplier_overview' span two columns
            df_html = df_html.replace('<th>supplier_overview</th>', '<th colspan="8" class="wrap-column">supplier_overview</th>')
    
            # Add custom CSS to wrap text in the column headers
            st.markdown(
                """
                <style>
                   .styled-table {
                        border: 2px solid yellow; /* Yellow border around the entire table */
                        border-radius: 10px; 

                        padding: 10px;
                        width: 100%;
                        box-sizing: border-box;
                        background-color: transparent;  /* Transparent background for the table */
                    }
                    
                    .styled-table th, .styled-table td {
                        border: none;  /* Remove borders between cells */
                        padding: 8px;
                        text-align: left;/
                        word-wrap: break-word;  /* Wrap text within cells */
                        white-space: normal;    /* Allow text wrapping */
                    }
                    
                    .styled-table th {
                        background-color: transparent;  /* Yellow background for header cells */
                        word-wrap: break-word;      /* Wrap text within header */
                        white-space: normal;        /* Allow text wrapping */
                    }
                    
                    .wrap-column {
                        word-wrap: break-word;
                        white-space: normal;
                        width: 200px; /* Adjust this width to suit your needs */
                    }
                    
                        }
                </style>

                """, 
                unsafe_allow_html=True
            )
    
            # Display the modified HTML table
            st.markdown(df_html, unsafe_allow_html=True)  # Display the HTML table
            
            # Store the DataFrame for future queries
            st.session_state.previous_results.append(df)  
        else:
            st.write("No results found based on the query.")
    else:
        st.write('Query Empty')






   
