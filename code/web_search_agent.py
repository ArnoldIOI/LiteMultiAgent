import logging
from dotenv import load_dotenv
from openai import OpenAI
import subprocess
from typing import Any
from pydantic import BaseModel, validator
import requests
import os
# from multion.client import MultiOn
from bs4 import BeautifulSoup
import json
_ = load_dotenv()
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log.txt", mode="w"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from langchain_community.tools.tavily_search import TavilySearchResults
from utils import *

def tavily_search(query):
    tool = TavilySearchResults(max_results=4)
    results = tool.invoke({"query": query})
    return results


def multion_search(query, url):
    multion = MultiOn(api_key=os.getenv('MULTION_API_KEY'))
    browse = multion.browse(
        cmd=query,
        url=url
    )
    print("Browse response:", browse)
    print(browse.message)
    return browse.message

def bing_search(query:str):
    search_url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv('BING_API_KEY')
    }
    params = {
        "q": query,
        "textDecorations": True, 
        "textFormat": "HTML"
    }
    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()
    except Exception as ex:
        raise ex
    # limit web page 
    pages = search_results["webPages"]["value"]
    n_web = min(10, len(pages))
    search_results["webPages"]["value"] = pages[:n_web]
    return search_results

def scrape(url: str):
    # scrape website. Url is the url of the website to be scraped
    print("Scraping website...")
    try:
        # Send a GET request to the URL
        response = requests.get(url)        
        # Check if the request was successful
        response.raise_for_status()        
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')        
        # Extract the text from the parsed HTML
        text = soup.get_text(separator=' ', strip=True)                
        return text
                
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return ""


tools = [
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "tavily_search",
    #         "description": "Perform a search using the TavilySearch API and return the results.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "query": {
    #                     "type": "string",
    #                     "description": "The search query to be sent to the TavilySearch API."
    #                 }
    #             },
    #             "required": [
    #                 "query"
    #             ]
    #         }
    #     }
    # },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "multion_search",
    #         "description": "For complicated search that require browsing/ scrolling down behavior, use multion api and return the results.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "query": {
    #                     "type": "string",
    #                     "description": "The search query to be sent to the multion API."
    #                 },
    #                 "url":{
    #                     "type": "string",
    #                     "description": "The website where multion api starts the browsing activity."
    #                 }
    #             },
    #             "required": [
    #                 "query",
    #                 "url"
    #             ]
    #         }
    #     }
    # },
    {
        "type": "function",
        "function": {
            "name": "bing_search",
            "description": "Bing search for relevant information given a query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Bing search query."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape",
            "description": "Scraping website content based on url from Bing search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website url to scrape."
                    }
                },
                "required": ["url"]
            }
        }
    },
]

from config import agent_to_model
agent_name = "web_search_agent"

available_tools = {
            # "tavily_search": tavily_search,
            # "multion_search": multion_search,
            "bing_search": bing_search,
            "scrape" : scrape
        }

def use_web_search_agent(query):
    messages = [{"role":"system", "content" :"You are a smart research assistant. Use the search engine to look up information."}]
    # send_prompt(messages, query)
    send_prompt("web_search_agent", messages, query, tools, available_tools)
    return messages[-1]["content"]


def main():
    messages = use_web_search_agent("Fetch the UK's GDP over the past 5 years")
    print(messages)
    # messages = use_web_search_agent(
    #     "browse google.com to check the brands of dining table and summarize the results in a table")
    # print(messages)

if __name__ == "__main__":
    main()
