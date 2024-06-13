from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_conn():
    conn = sqlite3.connect("issues.db")
    return conn

# Routing

@app.route("/")
def home():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM issues")
    issues = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("index.html", issues=issues)

@app.route("/add", methods = ["GET", "POST"])
def add_issue():

    if request.method == "POST":
        conn = get_conn()
        cursor = conn.cursor()
        title = request.form["title"]
        description = request.form["description"]
        status = "Open"
        cursor.execute("INSERT INTO issues (title, description, status) VALUES (?, ?, ?)", (title, description, status))
        conn.commit()
        cursor.close()
        conn.close()

    return render_template("new_issue.html")

@app.route("/issue_<int:id>", methods=["GET", "POST"])
def issue(id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM issues WHERE id = ?", (id,))
    issue = cursor.fetchone()
    
    if request.method == "POST":
        new_status = request.form["status"]
        cursor.execute("UPDATE issues SET status = ? WHERE id = ?", (new_status, id))
        conn.commit()

    cursor.close()
    conn.close()

    return render_template("issue.html", issue = issue)

if __name__ == '__main__':
    app.run(debug=True)