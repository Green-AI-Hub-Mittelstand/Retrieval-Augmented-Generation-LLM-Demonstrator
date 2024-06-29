from flask import Flask, request, jsonify, render_template, url_for, redirect
from bs4 import BeautifulSoup
from mlx_lm import load, generate
from llm import LLM
import threading
from rag import RAG
import deepl
from energy import PowerMetricsMonitor
import time
import os
import requests
import re

app = Flask(__name__)

def generate_text(llm, tokenizer, tasks, translator):
    while True:
        open_tasks = [task_id for task_id, task in tasks.items() if task["result"] == ""]
        if len(open_tasks) == 0:
            time.sleep(0.1)
            continue
        else:
            # new_prompt = translator.translate_text(prompt, target_lang="EN-US")
            prompt = tasks[open_tasks[0]]["prompt"]
            task_id = open_tasks[0]
            print("Dealing with task", task_id)
            prompt = f"<s>[INST] 'You are a assistant who answers the following question. Question: {prompt}[/INST] "
            result = generate(llm, tokenizer, prompt=prompt, verbose=False, max_tokens=1000, repetition_penalty=1.1)
            # translated_output = translator.translate_text(result, target_lang=new_prompt.detected_source_lang)
            tasks[task_id]["result"] = result   

@app.route('/')
def index():
    return redirect(url_for('homeDE'))

@app.route('/homeDE')
def homeDE():
    return render_template('index.html')

@app.route('/homeEN')
def homeEN():
    return render_template('indexEN.html')

@app.route('/wikiDE')
def wikiDE():
    return render_template('wikiDE.html')   

@app.route('/wikiEN')
def wikiEN():
    return render_template('wikiEN.html')  

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        # Parse the JSON data sent in the request body
        data = request.get_json()

        # You can now use the 'input' value sent from the client
        user_input = data['input']

        task_id = max(llm_tasks.keys()) + 1

        # Store the thread in the tasks dictionary
        llm_tasks[task_id] = {"result":"", "prompt":user_input, "start": time.time()}
        rag_tasks[task_id] = {"result":"", "prompt":user_input, "start": None}

        # Prepare the response data
        response_data = {'task_id': task_id}

        # Send a JSON response containing the processed data
        return jsonify(response_data)   
    else:
        # Falls der Request nicht POST ist, eine Fehlermeldung zurückgeben
        return jsonify({'error': 'Invalid request method'}), 405


@app.route('/submitwiki', methods=['POST'])
def submitwiki():
    if request.method == 'POST':
        # Parse the JSON data sent in the request body
        data = request.get_json()
        print(data) 

        # You can now use the 'input' value sent from the client
        user_input = data['input']
        print(user_input)

        # Check if the input is a Wikipedia URL
        if re.match(r'^https://de\.wikipedia\.org/wiki/', user_input):
            # HTML-Inhalt der URL abrufen
            response = requests.get(user_input)

            # Prüfen, ob die Anfrage erfolgreich war
            if response.status_code == 200:
                # Den HTML-Inhalt der Seite erhalten
                html_content = response.text
                
                # Den HTML-Inhalt mit BeautifulSoup analysieren
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Get the page title
                page_title = soup.find('h1', class_="firstHeading").get_text()

                # Find the content body using the class names
                content_body = soup.find('div', class_="mw-content-ltr mw-parser-output")
                if not content_body:
                    return jsonify({'error': 'Content body not found'}), 500

                paragraphs = content_body.find_all('p')

                # Find all headers with class mw-headline
                sections = content_body.find_all(class_="mw-headline")
                section_names = [section.get_text() for section in sections]

                chunked_data = []
                current_section = page_title # As default

                for idx, p in enumerate(paragraphs):
                    # Find the previous header to get the current section
                    previous = p.find_previous(class_="mw-headline")
                    if previous and previous.get_text() in section_names:
                        current_section = previous.get_text()
                    
                    paragraph_text = p.get_text()
                    if paragraph_text.strip():
                        chunked_data.append({
                            "text": paragraph_text,
                            "section": current_section,
                            "title": page_title,
                            "url": user_input,
                            "paragraph_index": idx
                        })

                # Prepare documents, metadata, and ids
                documents = [chunk["text"] for chunk in chunked_data]
                metadata = [{"url": chunk["url"], "title": chunk["title"], "section": chunk["section"], "paragraph_index": chunk["paragraph_index"]} for chunk in chunked_data]
                ids = [f"{user_input}_{idx}" for idx in range(len(chunked_data))]

                task_id = max(database_tasks.keys()) + 1

                # Store information about the database task
                database_tasks[task_id] = {"result": "", "prompt": user_input, "start": time.time()}

                # Create a new thread to generate the text
                thread = threading.Thread(target=rag.add_to_database, args=(documents, metadata, database_tasks, ids, task_id), daemon=True)
                thread.start()

                # Prepare the response data
                response_data = {'task_id': task_id}

                # Send a JSON response containing the processed data
                return jsonify(response_data), 200
            else:
                # Falls die Anfrage fehlschlägt, eine entsprechende Fehlermeldung zurückgeben
                return jsonify({'error': 'Failed to fetch URL'}), 500
        else:
            # Falls die URL keine Wikipedia-URL ist, eine Fehlermeldung zurückgeben
            return jsonify({'error': 'Invalid Wikipedia URL'}), 400
    else:
        # Falls der Request nicht POST ist, eine Fehlermeldung zurückgeben
        return jsonify({'error': 'Invalid request method'}), 405

    
@app.route('/status/llm/<taskId>', methods=['GET'])
def statusLLM(taskId):
    if llm_tasks[int(taskId)]["result"] == "":
        return jsonify({'status': 'PENDING'})
    else:
        time_difference = int(time.time() - llm_tasks[int(taskId)]["start"])
        rag_tasks[int(taskId)]["start"] = time.time()
        electricity = sum(power.cpu_power[-1 * time_difference:]) + sum(power.gpu_power[-1 * time_difference:])
        electricity = int(electricity / 3600)
        return jsonify({'status': 'COMPLETE', 'result': llm_tasks[int(taskId)]["result"], 'electricity': electricity})
    
@app.route('/status/rag/<taskId>', methods=['GET'])
def statusRAG(taskId):
    if rag_tasks[int(taskId)]["result"] == "":
        return jsonify({'status': 'PENDING'})
    else:
        time_difference = int(time.time() - llm_tasks[int(taskId)]["start"])
        rag_tasks[int(taskId)]["start"] = time.time()
        electricity = sum(power.cpu_power[-1 * time_difference:]) + sum(power.gpu_power[-1 * time_difference:])
        electricity = int(electricity / 3600)
        return jsonify({'status': 'COMPLETE', 'result': rag_tasks[int(taskId)]["result"], 'electricity': electricity})


@app.route('/status/database/<taskId>', methods=['GET'])
def statusDatabase(taskId):
     # Check if the result for the task is available
    if database_tasks[int(taskId)]["result"] == "":
        return jsonify({'status': 'PENDING'})
    else:    
        # Update the start time of the task
        database_tasks[int(taskId)]["start"] = time.time()
        
        # Return status as COMPLETE along with the result and electricity consumption
        return jsonify({'status': 'COMPLETE', 'result': database_tasks[int(taskId)]["result"]})


if __name__ == '__main__':
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    AUTH_KEY = "TOKEN"
    translator = deepl.Translator(AUTH_KEY)
    power = PowerMetricsMonitor()
    power.start()
    time.sleep(10)
    model, tokenizer = load("mlx-community/Mistral-7B-Instruct-v0.2-8-bit-mlx")
    llm_tasks = {0: {"result": "Test", "prompt": "", "start": 0}}
    rag_tasks = {0: {"result": "Test", "prompt": "", "start": 0}}
    database_tasks ={0:""}
     # Create a new thread to generate the text
    thread = threading.Thread(target=generate_text, args=(model, tokenizer, llm_tasks, translator), daemon=True)
    thread.start()
    rag = RAG(translator, model, tokenizer, rag_tasks)
    app.run(debug=True, host="0.0.0.0", port=5001)
