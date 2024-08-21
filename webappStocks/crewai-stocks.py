#IMPORT DA LIBS
import json
import os
from datetime import datetime
import yfinance as yf

from crewai import Agent, Task, Crew, Process

from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults

import streamlit as st

# CRIANDO YAHOO FINANCE TOOL
def fetch_stock_price(ticket):
    stock = yf.download(ticket, start="2023-08-08", end="2024-08-08")
    return stock

yahoo_finance_tool = Tool(
    name="Yahoo Finance Tool",
    description="Fetches stock prices for {ticket} from the last year about a specific company from Yahoo Finance API",
    func=lambda ticket: fetch_stock_price(ticket)
)

# IMPORTANDO OPENAI LLM - GPT
os.environ['OPENAI_API_KEY'] = "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"
llm = ChatOpenAI(model="gpt-3.5-turbo")

stockPriceAnalyst = Agent(
    role= "Senior stock price Analyst",
    goal="Find the {ticket} stock price and analyses trends",
    backstory="""You're a highly experienced in analyzing the price of an specific stock
    and make predoctopm about its future priice""",
    verbose=True,
    llm=llm,
    max_inter= 5,
    memory= True,
    tools=[yahoo_finance_tool],
    allow_delegation=False
)


# In[ ]:


getStockPrice = Task(
   description= "Analyze the stock {ticket} price history and create a trend analyses of up, down or sideways",
   expected_output =""" Specify the current trend sotck price - up, down or sideways.
   eg. stock="AAPL, price UP"
""",
    agent= stockPriceAnalyst
)


# In[ ]:


# IMPORTANDO A TOOL DE SEARCH
search_tool = DuckDuckGoSearchResults(backend='news', num_results=10)


# In[ ]:


newsAnalyst = Agent(
    role= "Stock News Analyst",
    goal="""Create a short summary of the market news related to the stock {ticket} company. Specify the current trend - up, down or sideways with
    the news context. For each request stock asset, specify a number between 0 and 100, where 0 is extreme fear and 100 is extreme gree.""",
    backstory="""You're a higjly experienced in analyzing the market trend and news and have tracked assest for more then 10 years.

    You're also master level analysts in the tradicional markets and have deep understanding of human psychology.

    You understand news, theirs tittles and information, but you look at those with a health dose of skepticism.
    You consider also the source of the news articles.
    """,
    verbose=True,
    llm=llm,
    max_inter= 10,
    memory= True,
    tools=[search_tool],
    allow_delegation=False
)


# In[95]:


get_news= Task(
    description ="""Take the stock and always include BTC to it (if not request).
    Use the seach tool to seach each one individually.

    The current date is {datetime.now()}.

    Compose the results into a helpfull report""",
    expected_output = """A summary of the overall market and one sentence summary for each request asset.
    Include a fear/greed score for each asset based on the news. Use the format: 
    <STOCK ASSET>
    <SUMMARY BASED ON NEWS>
    <TREND PREDICTION>
    <FEAR/GREED SCORE>
    """,
    agent= newsAnalyst
)


# In[ ]:


stockAnalystWhite = Agent(
    role = "Senior Stock Analyst writer",
    goal= """Analyze the trends price and news and White an insighfull compelling and informative 3 paragraph long newsletter based on the stock report and price trend.""",
    backstory = """You're widely accepted ass the best stock analyst in the market. You understand complex concepts and create compelling stories
    and narrativesthat resonate with wider audiences.

    You understand macro factors and combine multiple theories - eg. cycle theory and fundamental analyses. 
    You're able to hold multiple opinions when analyzing anything. 
""",
    verbose = True,
    llm=llm,
    max_iter = 5,
    memory=True,
    allow_delegation = True
)




# In[ ]:


writeAnalyses = Task(
    description = """Use the stock price trend and the stock news report to create an analyses and write the newsletter about the {ticket} Company
    that is brief and highlights the most important points.
    Focus on the stock price trend, news and fear/greed score. What are the near future considerations? 
    Include the previous analyses of stock trend and the news summary.
""",
    expected_output= """An eloquent 3 paragraphs newsletter formated as markdown in an easy readable manner. In should contain:

    - 3 bullet executive summary
    - Introduction - set the overall picture and spike up the interest
    - main part provides the meat of the analysis including the news summay andthe fead/greed scores
    -summary - key facts and concrete future trend prediction - up, down or sideways.
""",
    agent = stockAnalystWhite, 
    context = [getStockPrice, get_news]
)




# In[96]:




crew = Crew(
    agents=[stockPriceAnalyst, newsAnalyst, stockAnalystWhite],
    tasks=[getStockPrice, get_news, writeAnalyses],
    verbose= 2, 
    process= Process.hierarchical,
    full_output=True,
    share_crew=False,
    manager_llm=llm,
    max_iter=15
)


results= crew.kickoff(inputs={'ticket': 'AAPL'})


results['final_output']


with st.sidebar:
    st.header('Enter the stock to Research')

    with st.form(key='research_form'):
        topic = st.text_input("Select the ticket")
        submit_button = st.form_submit_botto(label = "Run Research")

if submit_button:
    if not topic:
        st.error("Please fill the ticket field")
    else:
        results= crew.kickoff(inputs={'ticket': topic})

        st.subheader("Results of your reseach:")
        st.write(results['final_output'])