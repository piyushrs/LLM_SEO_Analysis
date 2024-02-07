from flask import Flask, render_template, request, jsonify, url_for
from flask_cors import CORS
import ollama
from bs4 import BeautifulSoup
import requests
import pandas as pd
import markdown

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('main.html')

@app.route('/test', methods=['POST', 'GET'])
def test():
    if request.method == 'POST':
        data = request.get_json()
        local_data = data.get("input_data")
        res = check_if_exists(local_data)
        if res is not None:
            res = res.replace("\n", " ")
            ans = markdown.markdown(res)
            return jsonify(result = ans)
        else:
            res = crawl(local_data)
            if "Your request failed due to this error:" in res:
                return f"Your request failed! {res}"
            else:
                ans = ask_llama(res)
                ans = ans.replace("\n", " ")
                ans = markdown.markdown(ans)
                write_in_csv(local_data, ans)
                return jsonify(result = ans)
    else:
        return render_template('main.html')

# get all contents from the webpage
def crawl(url):
    try:
        soup = BeautifulSoup(requests.get(url, timeout= 10).text, "html.parser")
        text = soup.get_text()
        text = text[11:-4].replace('-', ' ').replace('_',' ').replace('#update', ' ').replace('\n', ' ').strip()
        return text
    except TimeoutError:
        return f"Your request failed due to this error: {TimeoutError}"

def ask_llama(website_data):
    question = f"You are a SEO Consultant. Can you provide SEO (Search Engine Optimization) analysis for the given website content: {website_data}? Provide a detailed answer with proper formatting."
    # question = f"Give me a report that details a companies value proposition given the following website content: {website_data}. Also provide CTA for the given website data. Give a detailed answer."
    response = ollama.chat(model='llama2', messages=[
    {
        'role': 'assistant',
        'content': question,
    },
    ])
    return (response['message']['content'])

def write_in_csv(url, response):
    df = pd.read_csv("processed/processed.csv")
    new_df = pd.DataFrame({"url": [url], "response": [response]})
    new_df = pd.concat([df, new_df], ignore_index= True)
    new_df.to_csv("processed/processed.csv", index= False)

def check_if_exists(url):
    df = pd.read_csv("processed/processed.csv")
    res = df[df['url'] == url]["response"].to_list()
    if len(res) != 0:
        return res[0]
    else:
        return None

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 8080, debug = True)