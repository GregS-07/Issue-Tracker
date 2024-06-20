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

        # Non-archived issues
        cursor.execute("SELECT status, COUNT(*) AS count FROM issues WHERE archivedOn IS NULL GROUP BY status")
        issues_count = cursor.fetchall()
        
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

        # Creating and saving unarchived graph
        plt.bar(statuses, counts, color=colors)
        plt.savefig("static/images/issues_status_graph.png")

        # Clear memory
        plt.clf()

        # Archived issues
        cursor.execute("SELECT status, COUNT(*) AS count FROM issues WHERE archivedOn IS NOT NULL GROUP BY status")
        a_issues_count = cursor.fetchall()
        
        a_statuses = [row[0] for row in a_issues_count]
        a_counts = [row[1] for row in a_issues_count]

        # Define colors based on status for archived issues
        a_colors = []
        for status in a_statuses:
            if status == 'Open':
                a_colors.append('green')
            elif status == 'In-Progress':
                a_colors.append('yellow')
            elif status == 'Closed':
                a_colors.append('red')
            else:
                a_colors.append('gray')  # Default color for any other status

        # Set labels
        plt.ylabel("Archived Issues")
        plt.xlabel("Status")    
        plt.title("Total Archived Issues By Status")

        # Set y-axis to display whole numbers
        plt.gca().yaxis.set_major_locator(plt.MaxNLocator(integer=True))

        # Creating and saving archived graph
        plt.bar(a_statuses, a_counts, color=a_colors)
        plt.savefig("static/images/issues_archived_status_graph.png")

        # Clear memory
        plt.clf()

        # Creating and saving archived vs unarchived pie chart

        # Calculating totals
        total = sum(counts)
        a_total = sum(a_counts)

        plt.pie([total, a_total] , colors=["red", "green"],  labels=[f"Archived Issues - {total}", f"Unarchived Issues {a_total}"])
        plt.title("Total Archived Issues & Unarchived Issues")
        plt.axis('equal') 
        plt.savefig("static/images/issues_archived_unarchived_total.png")

        # Clear memory
        plt.clf()
        

# Route to display all issues
@app.route("/")
def home():
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM issues WHERE archivedOn IS NULL")
        issues = cursor.fetchall()

        cursor.execute("SELECT * FROM issues WHERE archivedOn IS NOT NULL")
        archived_issues = cursor.fetchall()

    create_graph()

    return render_template("index.html", issues=issues, archived_issues=archived_issues)

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
@app.route("/issue_<int:id>", methods=["GET", "POST"])
def issue(id):
    if request.method == "GET":
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM issues WHERE id = ?", (id,))
            issue = cursor.fetchone()

            print(issue[4])
        return render_template("issue.html", issue=issue)

    if request.method == "POST":
        if request.form.get("_method") == "DELETE":
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM issues WHERE id = ?", (id,))
                conn.commit()
            return redirect(url_for("home"))  # Redirect to home after deleting issue
        elif request.form.get("_method") == "ARCHIVE":
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT archivedOn FROM issues WHERE id = ?", (id,))
                issue = cursor.fetchone()
                print(issue)
                if issue[0] is None:
                    cursor.execute('''
                        UPDATE issues
                        SET archivedOn = DATE('now')
                        WHERE id = ?
                    ''', (id,))
                    conn.commit()
                else:
                    cursor.execute('''
                        UPDATE issues
                        SET archivedOn = NULL
                        WHERE id = ?
                    ''', (id,))
                    conn.commit()

            return redirect(url_for("home", id=id))  # Redirect to home after updating status
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
                if request.form.get("include-archived"):
                    cursor.execute("SELECT * FROM issues WHERE (title LIKE ? OR description LIKE ?)", ('%' + search_query + '%', '%' + search_query + '%'))
                else:
                    cursor.execute("SELECT * FROM issues WHERE (title LIKE ? OR description LIKE ?) AND archivedOn IS NULL", ('%' + search_query + '%', '%' + search_query + '%'))

            issues = cursor.fetchall()

    return render_template("search.html", issues=issues)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)