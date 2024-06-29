import sqlite3
import deepl
import configparser

def read_config(config_path):
    # Create a ConfigParser object
    config = configparser.ConfigParser()
 
    # Read the configuration file
    config.read(config_path)

    auth_key = "TOKEN"
    return auth_key

def translate_text(text):
    result = translator.translate_text(text, source_lang="DE", target_lang="EN-GB")
    return result.text

def translate_db(db_path, db_path_transl):
    con = sqlite3.connect(db_path)
    con2 = sqlite3.connect(db_path_transl)
    cur = con.cursor()
    cur2 = con2.cursor()

    cur.execute("SELECT sql FROM sqlite_schema WHERE type='table'")
    commands = cur.fetchall()
    #create the same tables in the translated database
    for command in commands:
        command = str(command).strip('(\',)')
        command = command.replace('\\n\\t', '\n')
        command = command.replace('\\n', '\n')
        command = command + ")"
        command = command.replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS')
        cur2.execute(str(command))


    cur.execute("SELECT name FROM sqlite_schema WHERE type='table' ")
    tables = cur.fetchall()

    for table in tables: 
        table = str(table).strip('(,\')')
        cur.execute("SELECT * FROM " + table)
        rows = cur.fetchall()
        #translate the content for every project and write the translated version into the new database
        for row in rows:
            content = str(row[2]).replace('\\xa0', '\n')
            content = content.replace('\\n', '\n')
            content = translate_text(content)
            content = content.replace('\"', '')
            keep.append(content)
            with open(keep_path, 'w') as f: 
                f.write(str(keep))
            content = content.replace('\'', '')
            content = content.replace("'", '')
            cur2.execute("INSERT INTO " + table + " VALUES ("+str(row[0])+", '"+str(row[1])+"', '" +content+ "')")
    con2.commit()
    con2.close()


keep = []
config_path = "crawler/config.ini"
keep_path = 'crawler/content.txt'
auth_key = read_config(config_path)
translator = deepl.Translator(auth_key)

db_path = "crawler/green-ai-projekte.db"
db_path_transl = "crawler/green-ai-projekte-eng.db"

translate_db(db_path, db_path_transl)
