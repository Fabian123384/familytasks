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
# Level berechnen
# -----------------------------

def calculate_level(points):
    if points < 50:
        return 1
    elif points < 100:
        return 2
    elif points < 200:
        return 3
    elif points < 400:
        return 4
    elif points < 700:
        return 5
    elif points < 1000:
        return 6
    else:
        return 7

def level_progress(points):
    levels = [0, 50, 100, 200, 400, 700, 1000]
    level = calculate_level(points)

    if level >= 7:
        return 100, levels[level-1], levels[level-1]

    current_min = levels[level-1]
    next_level = levels[level]

    progress = int(((points - current_min) / (next_level - current_min)) * 100)
    return progress, current_min, next_level

# -----------------------------
# Startseite
# -----------------------------

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    role = users[user]["role"]

    points = users[user].get("points", 0)
    progress, current_min, next_level = level_progress(points)

    return render_template(
        "index.html",
        user=user,
        role=role,
        users=users,
        progress=progress,
        current_min=current_min,
        next_level=next_level
    )

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
            "points": 0,
            "level": 1
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

    tasks[index]["done"] = True

    assigned = tasks[index].get("assigned_to", "")
    points = tasks[index].get("points", 0)

    # Nur der zugewiesene Benutzer darf erledigen
if assigned != session["user"]:
    return redirect("/tasks")

# Punkte & Level aktualisieren
users[assigned]["points"] = users[assigned].get("points", 0) + points
users[assigned]["level"] = calculate_level(users[assigned]["points"])
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
