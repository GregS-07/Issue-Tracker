from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = b"6gtaptngf65/;g'7/e35#3]"

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

        #error may occur due to lack of input
        if total > 0 or a_total > 0:
            plt.pie([total, a_total], colors=["red", "green"], labels=[f"Archived Issues - {total}", f"Unarchived Issues - {a_total}"])
        else:
            plt.pie([1, 1], colors=["red", "green"], labels=[f"No Archived Issues", f"No Unarchived Issues"])
        plt.title("Total Archived Issues & Unarchived Issues")
        plt.axis('equal') 
        plt.savefig("static/images/issues_archived_unarchived_total.png")

        plt.clf()
        

# Route to login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, password FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user and user[1] == password:
                # Store user information in session
                session['username'] = user[0]
                session['password'] = user[1]
                return redirect(url_for('home'))
            else:
                return render_template("login.html", error="Incorrect username or password")
            
            db_password = user[0]
            
            if db_password == password:
                return redirect(url_for("home"))
            else:
                return redirect(url_for("login"))
        
    elif request.method == "GET":
        return render_template("login.html")

# Route to signup
@app.route("/signup", methods=["GET", "POST"])
def signup():

    # In case of unanticipated error
    error = "Failed due to an error. Please try again"
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        password_confirm = request.form["password-confirm"]


        if password != password_confirm:
            error="Passwords don't match"
        else:
            with get_conn() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()

                # SQLite doesn't enforce "UNIQUE" constraint so I have to check that it doesn't exist myself
                if result is None:
                    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                    return redirect(url_for("login"))
                else:
                    error="Username already exists"

                conn.commit()
            
        return render_template("signup.html", error=error)
    
    elif request.method == "GET":
        return render_template("signup.html")

@app.route("/account")
def account():
    return render_template("account.html")

@app.route("/view_<user>")
def user_page(user):
    # Getting issues
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM issues WHERE user = ? AND archivedOn IS NULL", (user,))
        issues = cursor.fetchall()

        cursor.execute("SELECT * FROM issues WHERE user = ? AND archivedOn IS NOT NULL", (user,))
        archived_issues = cursor.fetchall()

    return render_template("user.html", username=user, issues=issues, archived_issues=archived_issues)

# Route to display all issues
@app.route("/")
def home():
    # If user isn't logged in, there will be an error which will redirect the user to the login page
    try:
        session["username"]
    except:
        return redirect(url_for("login"))

    # Getting issues
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
            cursor.execute("INSERT INTO issues (title, description, status, user) VALUES (?, ?, ?, ?)", (title, description, status, session["username"]))
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
                cursor.execute("DELETE FROM issues WHERE id = ?", (id,)) # Deleting issues of deleted account
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
                if not request.form.get("exclude-other"):
                    if request.form.get("include-archived"):
                        cursor.execute("SELECT * FROM issues WHERE (title LIKE ? OR description LIKE ?)", ('%' + search_query + '%', '%' + search_query + '%'))
                    else:
                        cursor.execute("SELECT * FROM issues WHERE (title LIKE ? OR description LIKE ?) AND archivedOn IS NULL", ('%' + search_query + '%', '%' + search_query + '%'))
                else:
                    if request.form.get("include-archived"):
                        cursor.execute("SELECT * FROM issues WHERE (title LIKE ? OR description LIKE ?) AND user = ?", ('%' + search_query + '%', '%' + search_query + '%', session["username"]))
                    else:
                        cursor.execute("SELECT * FROM issues WHERE (title LIKE ? OR description LIKE ?) AND archivedOn IS NULL AND user = ?", ('%' + search_query + '%', '%' + search_query + '%', session["username"]))

            issues = cursor.fetchall()

    return render_template("search.html", issues=issues)

@app.route("/logout", methods=["POST"])
def logout():
    if request.method == "POST":
        session.clear()
        return redirect(url_for("home"))

@app.route("/delete_account", methods=["POST"])
def delete_account():
    if request.method == "POST":
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = ?", (session["username"],))
            cursor.execute("DELETE FROM issues WHERE user = ?", (session["username"],))
    session.clear()
    return redirect(url_for("home"))

# Handling user trying to access a page that doesn't exist
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)