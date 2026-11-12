# ai aget that has access to different data sources ie.e api's will get us info and give us structures proper response and also when to use which tool.
# using bright data to get info from google, bing, gpt, etc. and to not get blocked
# 

import os
import time

import requests
from dotenv import load_dotenv

from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuild import create_react_agent
from langgraph.graph import Stategraph, END, START

load_dotenv()

BRIGHTDATA_API_KEY=os.getenv('BRIGHTDATA_API_KEY')
BRIGHTDATA_SERP_ZONE=os.getenv('BRIGHTDATA_SERP_ZONE')
BRIGHTDATA_GPT_DATASET_ID=os.getenv('BRIGHTDATA_GPT_DATASET_ID')
BRIGHTDATA_PERPLEXITY_DATASET_ID=os.getenv('BRIGHTDATA_PERPLEXITY_DATASET_ID')


HEADERS = {
  'Authorization': f'Bearer {BRIGHTDATA_API_KEY}',
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}

@tool(description='Search using google.')
def google_search(query):
  print('Google is being used...')

  payload = {
    'zone': BRIGHTDATA_SERP_ZONE,
    'url': f'https://google.com/search?q={requests.utils.quote(query)}&brd_json=1',
    'format': 'raw',
    'country': 'US'
  }

  data = requests.post('https://api.brightdata.com/request?async=true', headers=HEADERS, json=payload).json()

  results = []

  for item in data.get('organic'):
    results.append(f"Title: {item[f'title]}\nLink: {item['Link']}\nSnippet: {item.get('description', '')}")

  return '\n\n'.join(results)[:10000]


@tool(description='Search using bing.')
def bing_search(query):
  print('Bing is being used...')

  payload = {
    'zone': BRIGHTDATA_SERP_ZONE,
    'url': f'https://bing.com/search?q={requests.utils.quote(query)}&brd_json=1',
    'format': 'raw',
    'country': 'US'
  }

  data = requests.post('https://api.brightdata.com/request?async=true', headers=HEADERS, json=payload).json()

  results = []

  for item in data.get('organic'):
    results.append(f"Title: {item[f'title]}\nLink: {item['Link']}\nSnippet: {item.get('description', '')}")

  return '\n\n'.join(results)[:10000]


@tool(description='Search using reddit.')
def reddit_search(query):
  print('Reddit is being used...')

  payload = {
    'zone': BRIGHTDATA_SERP_ZONE,
    'url': f'https://google.com/search?q={requests.utils.quote('site:reddit.com ' + query)}&brd_json=1',
    'format': 'raw',
    'country': 'US'
  }

  data = requests.post('https://api.brightdata.com/request?async=true', headers=HEADERS, json=payload).json()

  results = []

  for item in data.get('organic'):
    results.append(f"Title: {item[f'title]}\nLink: {item['Link']}\nSnippet: {item.get('description', '')}")

  return '\n\n'.join(results)[:10000]


@tool(description='Search using X.')
def x_search(query):
  print('X is being used...')

  payload = {
    'zone': BRIGHTDATA_SERP_ZONE,
    'url': f'https://google.com/search?q={requests.utils.quote('site:x.com ' + query)}&brd_json=1',
    'format': 'raw',
    'country': 'US'
  }

  data = requests.post('https://api.brightdata.com/request?async=true', headers=HEADERS, json=payload).json()

  results = []

  for item in data.get('organic'):
    results.append(f"Title: {item[f'title]}\nLink: {item['Link']}\nSnippet: {item.get('description', '')}")

  return '\n\n'.join(results)[:10000]


@tool(description='Use ChatGPT to get answer to a question.')
def prompt_gpt(query):
  print("GPT is being used...")

  payload = [
    {
      "url": "https://chatgpt.com",
      "prompt": query
    }
  ]

  url = f'https://api.brightdata.com/datasets/v3/trigger?dataset_id={BRIGHTDATA_GPT_DATASET_ID}&format=json&custom_output_fields=answer_text_markdown'

  response = requests.post(url, headers=HEADERS, json=payload)

  snapshot_id = 






  