# -*- coding: utf-8 -*-
"""sum_app.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1xLaTHOFVNWHSQbhbZOcEty4WCjQ2YF0N
"""

import validators, re
from fake_useragent import UserAgent
from bs4 import BeautifulSoup   
import streamlit as st
from transformers import pipeline
import time
import base64 
import requests
import docx2txt
from io import StringIO
from PyPDF2 import PdfFileReader
import warnings
import nltk

nltk.download('punkt')

from nltk import sent_tokenize

warnings.filterwarnings("ignore")

time_str = time.strftime("%d%m%Y-%H%M%S")

def article_text_extractor(url: str):
    
    
    ua = UserAgent()

    headers = {'User-Agent':str(ua.chrome)}

    r = requests.get(url,headers=headers)
    
    soup = BeautifulSoup(r.text, "html.parser")
    title_text = soup.find_all(["h1"])
    para_text = soup.find_all(["p"])
    article_text = [result.text for result in para_text]
    
    try:
    
        article_header = [result.text for result in title_text][0]
        
    except:
    
        article_header = ''
        
    article = " ".join(article_text)
    article = article.replace(".", ".<eos>")
    article = article.replace("!", "!<eos>")
    article = article.replace("?", "?<eos>")
    sentences = article.split("<eos>")
    
    current_chunk = 0
    chunks = []
    
    for sentence in sentences:
        if len(chunks) == current_chunk + 1:
            if len(chunks[current_chunk]) + len(sentence.split(" ")) <= 500:
                chunks[current_chunk].extend(sentence.split(" "))
            else:
                current_chunk += 1
                chunks.append(sentence.split(" "))
        else:
            print(current_chunk)
            chunks.append(sentence.split(" "))

    for chunk_id in range(len(chunks)):
        chunks[chunk_id] = " ".join(chunks[chunk_id])

    return article_header, chunks

def chunk_clean_text(text):

    sentences = sent_tokenize(text)
    current_chunk = 0
    chunks = []
    
    for sentence in sentences:
        if len(chunks) == current_chunk + 1:
            if len(chunks[current_chunk]) + len(sentence.split(" ")) <= 500:
                chunks[current_chunk].extend(sentence.split(" "))
            else:
                current_chunk += 1
                chunks.append(sentence.split(" "))
        else:
            print(current_chunk)
            chunks.append(sentence.split(" "))
    
    for chunk_id in range(len(chunks)):
        chunks[chunk_id] = " ".join(chunks[chunk_id])
    
    return chunks

def preprocess_plain_text(x):

    x = x.encode("ascii", "ignore").decode()  # unicode
    x = re.sub(r"https*\S+", " ", x)  # url
    x = re.sub(r"@\S+", " ", x)  # mentions
    x = re.sub(r"#\S+", " ", x)  # hashtags
    x = re.sub(r"\s{2,}", " ", x)  # over spaces
    x = re.sub("[^.,!?A-Za-z0-9]+", " ", x)  # special charachters except .,!?

    return x

def extract_pdf(file):
    
    
    pdfReader = PdfFileReader(file)
    count = pdfReader.numPages
    all_text = ""
    for i in range(count):
        page = pdfReader.getPage(i)
        all_text += page.extractText()
    

    return all_text

def extract_text_from_file(file):

    if file.type == "text/plain":

        stringio = StringIO(file.getvalue().decode("utf-8"))
        file_text = stringio.read()

    elif file.type == "application/pdf":
        file_text = extract_pdf(file)

    elif (
        file.type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        file_text = docx2txt.process(file)

    return file_text

def summary_downloader(raw_text):
    
	b64 = base64.b64encode(raw_text.encode()).decode()
	new_filename = "new_text_file_{}_.txt".format(time_str)
	st.markdown("#### Download Summary as a File ###")
	href = f'<a href="data:file/txt;base64,{b64}" download="{new_filename}">Click to Download!!</a>'
	st.markdown(href,unsafe_allow_html=True)

@st.cache(allow_output_mutation=True)
def bart_model():
    
    summarizer = pipeline('summarization',model='facebook/bart-large-cnn')
    return summarizer
    
@st.cache(allow_output_mutation=True)
def distil_model():
    
    summarizer = pipeline('summarization',model='sshleifer/distilbart-cnn-12-6')
    return summarizer

st.title("Crossbar Summarizer for Content Creation")

model_type = st.sidebar.selectbox(
    "Model type", options=["BART_CTMS", "DistilBART_CTMS"]
)

max_len= st.sidebar.slider("Maximum length of the summarized text",min_value=80,max_value=500,step=10)
min_len= st.sidebar.slider("Minimum length of the summarized text",min_value=10,step=10)

st.markdown(
    "Model Source: [Bart](https://huggingface.co/adityawithdoublea/BART_finetuned_SciTLDR) and [DistilBart](https://huggingface.co/sshleifer/distilbart-cnn-12-6)"
)

st.markdown(
    """This project is part of our practice school project under Crossbar Talent and Management Solutions Pvt. Ltd.
    """)

st.markdown(""" For documents or text that is more than 500 words long, the app will divide those texts into small pieces of raw texts 
    with not more than 500 words and summarize each piece.""")

st.markdown("""Please note when using the sidebar slider, those values 
    represent the min/max text length per piece of text to be summarized. If your article to be summarized is 
    1000 words, it will be divided into two pieces of 500 words first then the default max length of 100 words is 
    applied per piece, resulting in a summarized text with 200 words maximum.""")

st.markdown(""" There are two models available to choose from:""")

st.markdown("""   
    - BART_CTMS, trained on large [CNN and Daily Mail] then fine-tuned on [SciTLDR](https://huggingface.co/datasets/scitldr)
    - DistilBart_CTMS, which is a distilled (smaller) version of the large BART model."""
)

st.markdown("""NOTE: The model will take longer to generate summaries for documents that are too long!""")

st.markdown(
    "The app currently only accepts the following formats for summarization task:"
)
st.markdown(
    """- Raw text(entered directly in the textbox)
- URL of an article
- Documents with .txt, .pdf or .docx file formats"""
)

st.markdown("---")

url_text = st.text_input("Enter/Paste a url below:")

st.markdown(
    "<h5 style='text-align: center; color: ##bababa;'>OR</h5>",
    unsafe_allow_html=True,
)

plain_text = st.text_input("Enter/Paste raw text below:")

st.markdown(
    "<h5 style='text-align: center; color: ##bababa;'>OR</h5>",
    unsafe_allow_html=True,
)

upload_doc = st.file_uploader(
    "Upload a file to summarize:"
)

is_url = validators.url(url_text)

if is_url:
    article_title,chunks = article_text_extractor(url=url_text)
    
elif upload_doc:
    
    clean_text = chunk_clean_text(preprocess_plain_text(extract_text_from_file(upload_doc)))

else:
    
    clean_text = chunk_clean_text(preprocess_plain_text(plain_text))

summarize = st.button("Summarize")

if summarize:
    if model_type == "BART_CTMS":
        if is_url:
            text_to_summarize = chunks
        else:
            text_to_summarize = clean_text

        with st.spinner(
            text="Loading BART_CTMS Model... This might take a few seconds depending on file size."
        ):
            summarizer_model = bart_model()
            summarized_text = summarizer_model(text_to_summarize, max_length=max_len, min_length=min_len)
            summarized_text = ' '.join([summ['summary_text'] for summ in summarized_text])
    
    elif model_type == "DistilBART_CTMS":
        if is_url:
            text_to_summarize = chunks
        else:
            text_to_summarize = clean_text

        with st.spinner(
            text="Loading DistilBART_CTMS Model... This might take a few seconds depending on file size."
        ):
            summarizer_model = distil_model()
            summarized_text = summarizer_model(text_to_summarize, max_length=max_len, min_length=min_len)
            summarized_text = ' '.join([summ['summary_text'] for summ in summarized_text])       
    
    # final summarized output
    st.subheader("Summarized text")
    
    if is_url:
    
        # view summarized text (expander)
        st.markdown(f"Article title: {article_title}")
        
    st.write(summarized_text)
    
    summary_downloader(summarized_text)


st.markdown("""
            """)
