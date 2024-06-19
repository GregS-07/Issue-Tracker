from flask import Flask, render_template, request, redirect, url_for
import sqlite3

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)

# Function to get a SQLite connection
def get_conn():
    conn = sqlite3.connect("issues.db")
    return conn

# Function to create issues graph
def create_graph():
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) AS count FROM issues GROUP BY status")
        issues_count = cursor.fetchall()
        
        # Converting the tuples into lists
        statuses = [row[0] for row in issues_count]
        counts = [row[1] for row in issues_count]

        # Define colors based on status 
        colors = []
        for status in statuses:
            if status == 'Open':
                colors.append('green')
            elif status == 'In-Progress':
                colors.append('yellow')
            elif status == 'Closed':
                colors.append('red')
            else:
                colors.append('gray')  # Default color for any other status

        # Set labels
        plt.ylabel("Issues")
        plt.xlabel("Status")    
        plt.title("Total Issues By Status")

        # Set y-axis to display whole numbers
        plt.gca().yaxis.set_major_locator(plt.MaxNLocator(integer=True))

        # Creating and saving graph
        plt.bar(statuses, counts, color=colors)
        plt.savefig("static/images/issues_status_graph.png")

        # Clear memory
        plt.clf()
        

# Route to display all issues
@app.route("/")
def home():
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM issues")
        issues = cursor.fetchall()

    create_graph()

    return render_template("index.html", issues=issues)

# Route to add a new issue
@app.route("/add", methods=["GET", "POST"])
def add_issue():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        status = "Open"
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO issues (title, description, status) VALUES (?, ?, ?)", (title, description, status))
            conn.commit()
        return redirect(url_for("home"))  # Redirect to home after adding issue
    return render_template("new_issue.html")

# Route to view and update/delete an issue
@app.route("/issue_<int:id>", methods=["GET", "POST", "DELETE"])
def issue(id):
    if request.method == "GET":
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM issues WHERE id = ?", (id,))
            issue = cursor.fetchone()
        return render_template("issue.html", issue=issue)

    if request.method == "POST":
        if request.form.get("_method") == "DELETE":
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM issues WHERE id = ?", (id,))
                conn.commit()
            return redirect(url_for("home"))  # Redirect to home after deleting issue
        else:
            new_status = request.form["status"]
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE issues SET status = ? WHERE id = ?", (new_status, id))
                conn.commit()
            return redirect(url_for("home", id=id))  # Redirect to home after updating status

@app.route("/search", methods=["GET", "POST"])
def search():
    issues = []
    if request.method == "POST":
        search_query = request.form["search"]

        with get_conn() as conn:
            cursor = conn.cursor()
            if search_query:
                cursor.execute("SELECT * FROM issues WHERE title LIKE ? OR description LIKE ?", ('%'+search_query+'%', '%'+search_query+'%'))

            issues = cursor.fetchall()

    return render_template("search.html", issues=issues)

if __name__ == '__main__':
    app.run(debug=True)