import chromadb
from chromadb.utils import embedding_functions # This helps us fetch our embedding model
from mlx_lm import load, generate
import sqlite3
import deepl
import time
import threading

class RAG:

    def __init__(self, translator, model, tokenizer, rag_tasks) -> None:
        self.embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="intfloat/multilingual-e5-large")
        self.client = chromadb.PersistentClient(path="./chromadb")
        self.__init_database()
        self.collection = self.client.get_or_create_collection(
            name=f"Green-AI",
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_model,
        )
        self.model, self.tokenizer = model, tokenizer
        self.translator = translator
        self.rag_tasks = rag_tasks
        threading.Thread(target=self.handle_tasks, daemon=True).start()

    def __split_string_in_half(self, s):
        # Split the string into words
        words = s.split()
        
        # Find the midpoint of the list of words
        mid_index = len(words) // 2
        
        # Adjust the midpoint for even division; you can modify this as needed
        if len(words) % 2 != 0:  # Check if the number of words is odd
            mid_index += 1  # Adjust so the first half gets the extra word
        
        # Split the list into two halves
        first_half_words = words[:mid_index]
        second_half_words = words[mid_index:]
        
        # Rejoin each half into a string
        first_half = ' '.join(first_half_words)
        second_half = ' '.join(second_half_words)
        
        return first_half, second_half

    def __init_database(self):
        collection_exists = "Green-AI" in [collection.name for collection in self.client.list_collections()]
        if not collection_exists:
            con = sqlite3.connect("crawler/mitteilungen.db")
            cur = con.cursor()

            mitteilungen = cur.execute("SELECT * FROM mitteilungen").fetchall()

            con = sqlite3.connect("crawler/green-ai-projekte-eng.db")
            cur = con.cursor()
            projekte = cur.execute("SELECT * FROM projekte").fetchall()

            collection = self.client.create_collection(
                name=f"Green-AI",
                metadata={"hnsw:space": "cosine"}, # l2 is the default
                embedding_function=self.embedding_model,
            )
            documents = []
            metadata = []
            ids = []
            # for mitteilung in mitteilungen:
            #     documents.append(mitteilung[2])
            #     metadata.append({"title": mitteilung[1]})
            #     ids.append("mitteilung " + str(mitteilung[0]))
            for projekt in projekte:
                document_text = projekt[2].replace("\t", " ")
                document_text = document_text.replace("\n", " ")
                document_text = document_text.replace("  ", " ")
                for i, current_text in enumerate(self.__split_string_in_half(document_text)):
                    documents.append(current_text)
                    metadata.append({"title": projekt[1]})
                    ids.append(f"projekt_{str(projekt[0])}_{i}")
            collection.add(
                documents=documents,
                metadatas=metadata,
                ids=ids,
            )

    def query(self, prompt):
        return self.collection.query(query_texts=prompt, n_results=1)


    def add_to_database(self, documents, metadata, tasks, ids, task_id):
        print("start adding to database")
        self.collection.add(
            documents=documents, 
            metadatas=metadata, 
            ids=ids
        )
        tasks[task_id]["result"] = "Added"


    def handle_tasks(self) -> str:
        while True:
            open_tasks = [task_id for task_id, task in self.rag_tasks.items() if task["result"] == "" and task["start"] != None]
            if len(open_tasks) == 0:
                time.sleep(0.1)
                continue
            else:
                print(open_tasks)
                # translated_text = self.translator.translate_text(prompt, target_lang="EN-US")
                task_id = open_tasks[0]
                prompt = self.rag_tasks[task_id]["prompt"]
                result = self.collection.query(
                    query_texts=prompt,
                    n_results=3,
                )
                # Concat documents
                document_string = "\n".join([result["documents"][0][0], result["documents"][0][1]])
                prompt = f"<s>[INST] Given the following data, answer the appended question: {document_string}\n Question: {prompt}[/INST] "
                # output = "Example text"
                output = generate(self.model, self.tokenizer, prompt=prompt, verbose=False, max_tokens=1000, repetition_penalty=1.1)
                translated_output = self.translator.translate_text(output, target_lang="DE")
                self.rag_tasks[task_id]["result"] = translated_output.text


   