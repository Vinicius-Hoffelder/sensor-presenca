from flask import Flask, request, jsonify
import sqlite3

app = Flask(_name_)

# Criação do banco
def criar_banco():
    con = sqlite3.connect("presencas.db")
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS presencas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        horario TEXT NOT NULL
    )
    """)
    con.commit()

    con.close()

criar_banco()

@app.route('/registrar', methods=['POST'])
def registrar():
    data = request.json.get("data")
    horario = request.json.get("horario")
    con = sqlite3.connect("presencas.db")
    cur = con.cursor()
    cur.execute("INSERT INTO presencas (data, horario) VALUES (?, ?)", (data, horario))
    con.commit()
    con.close()
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
