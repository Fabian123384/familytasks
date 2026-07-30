from flask import Flask, render_template, request, redirect, session
import json

app = Flask(__name__)
app.secret_key = "geheim123"

# -------------------------
# BENUTZER SPEICHERN / LADEN
# -------------------------

def load_users():
    with open("users.json", "r") as f:
        return json.load(f)

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

users = load_users()

tasks = []
terminal_output = ["Willkommen im Terminal!"]

# -------------------------
# STARTSEITE
# -------------------------

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    role = users[user]["role"]
    away = users[user]["away"]

    return render_template("index.html", tasks=tasks, user=user, role=role, away=away, users=users)

# -------------------------
# LOGIN
# -------------------------

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

# -------------------------
# LOGOUT
# -------------------------

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return redirect("/login")

# -------------------------
# REGISTER
# -------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in users:
            return render_template("register.html", error="Benutzername existiert bereits")

        users[username] = {"password": password, "role": "user", "away": False}
        save_users(users)

        session["user"] = username
        return redirect("/")

    return render_template("register.html")

# -------------------------
# AWAY-STATUS (Benutzer selbst)
# -------------------------

@app.route("/toggle_away", methods=["POST"])
def toggle_away():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    users[user]["away"] = not users[user]["away"]
    save_users(users)
    return redirect("/")

# -------------------------
# AUFGABEN HINZUFÜGEN
# -------------------------

@app.route("/add", methods=["POST"])
def add_task():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    role = users[user]["role"]

    if role not in ["admin", "user"]:
        return redirect("/")

    text = request.form.get("task")
    assigned_to = request.form.get("assigned_to")

    tasks.append({"text": text, "done": False, "assigned_to": assigned_to})
    return redirect("/")

# -------------------------
# AUFGABEN LÖSCHEN (nur Admin)
# -------------------------

@app.route("/delete", methods=["POST"])
def delete_task():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    role = users[user]["role"]

    if role != "admin":
        return redirect("/")

    text = request.form.get("task")
    for t in tasks:
        if t["text"] == text:
            tasks.remove(t)
            break

    return redirect("/")

# -------------------------
# AUFGABEN ALS ERLEDIGT MARKIEREN
# -------------------------

@app.route("/done", methods=["POST"])
def mark_done():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    role = users[user]["role"]

    text = request.form.get("task")

    for t in tasks:
        if t["text"] == text:
            if role == "admin" or user == t["assigned_to"]:
                t["done"] = True
            break

    return redirect("/")

# -------------------------
# TERMINAL (nur Admin)
# -------------------------

@app.route("/terminal", methods=["GET", "POST"])
def terminal():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    role = users[user]["role"]

    if role != "admin":
        return redirect("/")

    global terminal_output

    if request.method == "POST":
        cmd = request.form.get("command")

        if cmd == "help":
            terminal_output.append("Befehle: help, list, clear, add <text>, delete <text>, role <user> <role>, away <user> <on/off>")

        elif cmd == "list":
            if tasks:
                for t in tasks:
                    terminal_output.append(f"- {t['text']} (done: {t['done']}, assigned_to: {t['assigned_to']})")
            else:
                terminal_output.append("Keine Aufgaben vorhanden.")

        elif cmd.startswith("add "):
            terminal_output.append("Nutze die Webseite zum Zuweisen von Aufgaben.")

        elif cmd.startswith("delete "):
            text = cmd[7:]
            found = False
            for t in tasks:
                if t["text"] == text:
                    tasks.remove(t)
                    terminal_output.append(f"Aufgabe gelöscht: {text}")
                    found = True
                    break
            if not found:
                terminal_output.append("Aufgabe nicht gefunden.")

        elif cmd.startswith("role "):
            parts = cmd.split(" ")
            if len(parts) == 3:
                username = parts[1]
                new_role = parts[2]

                if username in users:
                    users[username]["role"] = new_role
                    save_users(users)
                    terminal_output.append(f"Rolle geändert: {username} → {new_role}")
                else:
                    terminal_output.append("Benutzer nicht gefunden.")
            else:
                terminal_output.append("Benutzung: role <benutzer> <rolle>")

        elif cmd.startswith("away "):
            parts = cmd.split(" ")
            if len(parts) == 3:
                username = parts[1]
                state = parts[2]

                if username in users:
                    if state == "on":
                        users[username]["away"] = True
                        save_users(users)
                        terminal_output.append(f"{username} ist jetzt NICHT im Haus")
                    elif state == "off":
                        users[username]["away"] = False
                        save_users(users)
                        terminal_output.append(f"{username} ist jetzt im Haus")
                    else:
                        terminal_output.append("Benutzung: away <user> on/off")
                else:
                    terminal_output.append("Benutzer nicht gefunden.")
            else:
                terminal_output.append("Benutzung: away <user> on/off")

        elif cmd == "clear":
            terminal_output = []

        else:
            terminal_output.append("Unbekannter Befehl. Tippe 'help'.")

    return render_template("terminal.html", output=terminal_output)

# -------------------------
# ADMIN-BEREICH
# -------------------------

@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    role = users[user]["role"]

    if role != "admin":
        return redirect("/")

    return render_template("admin.html", users=users, user=user, role=role)

# -------------------------
# ADMIN: Rolle ändern
# -------------------------

@app.route("/admin/set_role", methods=["POST"])
def admin_set_role():
    username = request.form.get("username")
    new_role = request.form.get("role")

    if username in users:
        users[username]["role"] = new_role
        save_users(users)

    return redirect("/admin")

# -------------------------
# ADMIN: Away ändern
# -------------------------

@app.route("/admin/toggle_away", methods=["POST"])
def admin_toggle_away():
    username = request.form.get("username")

    if username in users:
        users[username]["away"] = not users[username]["away"]
        save_users(users)

    return redirect("/admin")

# -------------------------
# ADMIN: Benutzer löschen
# -------------------------

@app.route("/admin/delete_user", methods=["POST"])
def admin_delete_user():
    username = request.form.get("username")

    if username in users:
        del users[username]
        save_users(users)

    return redirect("/admin")

# -------------------------
# ADMIN: Benutzer hinzufügen
# -------------------------

@app.route("/admin/add_user", methods=["POST"])
def admin_add_user():
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")

    if username not in users:
        users[username] = {"password": password, "role": role, "away": False}
        save_users(users)

    return redirect("/admin")

# -------------------------
# ADMIN: Passwort ändern
# -------------------------

@app.route("/admin/change_password", methods=["POST"])
def admin_change_password():
    username = request.form.get("username")
    new_pw = request.form.get("new_password")

    if username in users:
        users[username]["password"] = new_pw
        save_users(users)

    return redirect("/admin")

# -------------------------
# ADMIN: Namen ändern
# -------------------------

@app.route("/admin/change_name", methods=["POST"])
def admin_change_name():
    old_name = request.form.get("old_name")
    new_name = request.form.get("new_name")

    if old_name in users:
        users[new_name] = users.pop(old_name)
        save_users(users)

        # Falls der Benutzer gerade eingeloggt ist
        if "user" in session and session["user"] == old_name:
            session["user"] = new_name

    return redirect("/admin")
