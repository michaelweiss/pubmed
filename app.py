# -*- coding: utf-8 -*-
"""pubmed streamlit.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/15LnFY710nEwW5bXcYEJhBzePmaDDFuIZ
"""

import requests
from openai import OpenAI
from bs4 import BeautifulSoup

def search_pubmed(query_terms, max_articles=20):
    # Step 1: Perform a search and get a list of PubMed IDs
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        'db': 'pubmed',
        'term': ' '.join(query_terms),
        'retmax': max_articles  # Limit the number of articles
    }

    print(query_terms)

    response = requests.get(search_url, params=search_params)
    response_xml = response.text

    # Extract PubMed IDs and filter out articles without abstracts
    article_ids = [id for id in extract_pubmed_ids(response_xml) if has_abstract(id)]

    return article_ids[:max_articles]  # Return only the specified number of article IDs

def has_abstract(article_id):
    # Check if the article has an abstract
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    fetch_params = {
        'db': 'pubmed',
        'id': article_id,
        'retmode': 'xml',
    }

    response = requests.get(fetch_url, params=fetch_params)
    response_xml = response.text

    return '<AbstractText>' in response_xml

def extract_pubmed_ids(xml_response):
    # Parse the XML response and extract PubMed IDs
    article_ids = []
    for line in xml_response.split('\n'):
        if '<Id>' in line:
            article_ids.append(line.replace('<Id>', '').replace('</Id>', ''))
    return article_ids

def retrieve_abstract(article_id):
    # Retrieve abstract for a given PubMed ID
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    fetch_params = {
        'db': 'pubmed',
        'id': article_id,
        'retmode': 'xml',
    }

    response = requests.get(fetch_url, params=fetch_params)
    response_xml = response.text

    # Extract abstract from the XML response
    abstract_start = response_xml.find('<AbstractText>') + len('<AbstractText>')
    abstract_end = response_xml.find('</AbstractText>', abstract_start)

    if abstract_start != -1 and abstract_end != -1:
        abstract = response_xml[abstract_start:abstract_end].strip()
    else:
        abstract = "Abstract not available"

    return abstract

def generate_openai_completion(input_text, research_question):
    #Initialize OpenAI client
    client = OpenAI(api_key=userdata.get('openai'))

    # Response format
    response_format_begin = "Based on the retrieved abstracts, I think the answer to your question is:"

    # Convert input text to a more focused prompt
    prompt = f"Please answer this question: {research_question} using only the list of abstracts retrieved from PubMed here: {input_text}. Format your response by starting with {response_format_begin}. Be sure to answer a question directly, usually a yes or no, followed by supporting reasons you found in the abstracts."

    try:
        # Make a completion request to GPT-3
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=500
        )

        # Get the generated text from the response
        return response.choices[0].text

    except Exception as e:
        # Handle exceptions and print an error message
        print(f"Error: {e}")
        return None

def extract_pubmed_info(article_id):
    # Extract title and URL from PubMed for a given PubMed ID
    fetch_url = f"https://pubmed.ncbi.nlm.nih.gov/{article_id}"

    response = requests.get(fetch_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract title
    title_tag = soup.find('meta', attrs={'name': 'citation_title'})
    title = title_tag['content'] if title_tag else "Title not available"

    # Construct URL
    article_url = f"https://pubmed.ncbi.nlm.nih.gov/{article_id}/"

    return title, article_url

def generate_and_display_table(article_ids):
    st.subheader("Table of Retrieved Articles:")
    st.write("PubMed ID\tTitle\t\t\t\t\t\t\t\t\t\t\t\t\t\tURL")
    for article_id in article_ids:
        title, article_url = extract_pubmed_info(article_id)
        st.write(f"{article_id}\t\t{title}\t\t\t\t{article_url}")

def summarize_abstracts(article_ids, research_question):
    # Retrieve abstracts and accumulate them
    all_abstracts = ""
    for article_id in article_ids:
        abstract = retrieve_abstract(article_id)
        # print(f"PubMed ID: {article_id}\nAbstract:\n{abstract}\n{'='*30}")
        if abstract is not None:
            all_abstracts += abstract + "\n\n"

    # Send all abstracts and research question to openAI to answer
    summary = generate_openai_completion(all_abstracts, research_question)

    return summary

# Streamlit app
def main():
    st.title("PubMed Abstract Summarizer")

    # Get user question
    research_question = st.text_input("Enter a question:")

    # Get user input for search terms
    query_terms = st.text_input("Enter a list of terms separated by spaces:")

    # Call the function to search PubMed and retrieve abstracts
    article_ids = search_pubmed(query_terms.split())

    if article_ids:
        # Call the function to summarize the retrieved abstracts
        summary = summarize_abstracts(article_ids, research_question)

        # Display the generated summary
        st.subheader("Answer:")
        st.write(summary)

        # Display the table of retrieved articles
        generate_and_display_table(article_ids)

    else:
        st.warning("No articles found.")

if __name__ == "__main__":
    main()
