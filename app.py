from flask import Flask, render_template, request, redirect, session
import json
import os

app = Flask(__name__)
app.secret_key = "geheim123"

# -----------------------------
# JSON-Dateien laden & speichern
# -----------------------------

def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

def load_tasks():
    if os.path.exists("tasks.json"):
        with open("tasks.json", "r") as f:
            return json.load(f)
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
    return render_template("index.html", user=user, role=role)

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
# Logout (GET erlaubt)
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

        users[username] = {"password": password, "role": "user", "away": False}
        save_users(users)

        return redirect("/login")

    return render_template("register.html")

# -----------------------------
# Aufgaben
# -----------------------------

@app.route("/tasks", methods=["GET", "POST"])
def tasks_page():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        new_task = request.form.get("task")
        if new_task:
            tasks.append({"task": new_task, "done": False})
            save_tasks(tasks)

    return render_template("tasks.html", tasks=tasks)

# -----------------------------
# Aufgabe erledigt
# -----------------------------

@app.route("/task_done/<int:index>")
def task_done(index):
    tasks[index]["done"] = True
    save_tasks(tasks)
    return redirect("/tasks")

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
