from flask import Flask, render_template, request, redirect, session
import json

app = Flask(__name__)
app.secret_key = "geheim123"

# -----------------------------
# JSON laden & speichern
# -----------------------------

def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

def load_tasks():
    try:
        with open("tasks.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_tasks(tasks):
    with open("tasks.json", "w") as f:
        json.dump(tasks, f, indent=4)

users = load_users()
tasks = load_tasks()
terminal_output = ["Willkommen im Terminal!"]

# -----------------------------
# Startseite
# -----------------------------

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    role = users[user]["role"]
    return render_template("index.html", user=user, role=role, users=users)

# -----------------------------
# Login
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in users and users[username]["password"] == password:
            session["user"] = username
            return redirect("/")
        else:
            return render_template("login.html", error="Falscher Benutzer oder Passwort")

    return render_template("login.html")

# -----------------------------
# Logout
# -----------------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -----------------------------
# Register
# -----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in users:
            return render_template("register.html", error="Benutzer existiert bereits")

        users[username] = {
            "password": password,
            "role": "user",
            "away": False,
            "points": 0
        }
        save_users(users)

        return redirect("/login")

    return render_template("register.html")

# -----------------------------
# Aufgaben – Liste + hinzufügen
# -----------------------------

@app.route("/tasks", methods=["GET", "POST"])
def tasks_page():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        new_task = request.form.get("task")
        assigned_to = request.form.get("assigned_to")
        points_raw = request.form.get("points")

        # Punkte sicher auslesen
        try:
            points = int(points_raw)
        except:
            points = 0

        if new_task:
            tasks.append({
                "task": new_task,
                "done": False,
                "assigned_to": assigned_to or "",
                "points": points,
                "created_by": session["user"]
            })
            save_tasks(tasks)

    return render_template("tasks.html", tasks=tasks, users=users)


# -----------------------------
# Aufgabe erledigt
# -----------------------------

@app.route("/task_done/<int:index>")
def task_done(index):
    if index < 0 or index >= len(tasks):
        return redirect("/tasks")

    # Aufgabe als erledigt markieren
    tasks[index]["done"] = True

    # Sicher auslesen
    assigned = tasks[index].get("assigned_to", "")
    points = tasks[index].get("points", 0)

    # Punkte nur vergeben, wenn assigned_to ein gültiger Benutzer ist
    if assigned in users:
        users[assigned]["points"] = users[assigned].get("points", 0) + points
        save_users(users)

    save_tasks(tasks)
    return redirect("/tasks")


# -----------------------------
# Aufgabe löschen
# -----------------------------

@app.route("/task_delete/<int:index>")
def task_delete(index):
    if 0 <= index < len(tasks):
        tasks.pop(index)
        save_tasks(tasks)
    return redirect("/tasks")


# -----------------------------
# Aufgabe bearbeiten
# -----------------------------

@app.route("/task_edit/<int:index>", methods=["GET", "POST"])
def task_edit(index):
    if "user" not in session:
        return redirect("/login")

    if index < 0 or index >= len(tasks):
        return redirect("/tasks")

    if request.method == "POST":
        tasks[index]["task"] = request.form.get("task")
        tasks[index]["assigned_to"] = request.form.get("assigned_to") or ""

        # Punkte sicher auslesen
        points_raw = request.form.get("points")
        try:
            tasks[index]["points"] = int(points_raw)
        except:
            tasks[index]["points"] = 0

        save_tasks(tasks)
        return redirect("/tasks")

    return render_template("task_edit.html", task=tasks[index], index=index, users=users)


# -----------------------------
# Away-Status
# -----------------------------

@app.route("/away")
def away():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    users[user]["away"] = not users[user]["away"]
    save_users(users)

    return redirect("/")

# -----------------------------
# Admin-Terminal
# -----------------------------

@app.route("/terminal", methods=["GET", "POST"])
def terminal():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    if users[user]["role"] != "admin":
        return "Zugriff verweigert"

    global terminal_output

    if request.method == "POST":
        command = request.form.get("command")
        terminal_output.append(f"> {command}")

        if command == "users":
            terminal_output.append(str(users))
        elif command == "tasks":
            terminal_output.append(str(tasks))
        else:
            terminal_output.append("Unbekannter Befehl")

    return render_template("terminal.html", output=terminal_output)

# -----------------------------
# Start
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)
