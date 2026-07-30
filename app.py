from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "geheim123"

# Benutzer-Datenbank mit Rollen + Away-Status
users = {
    "Fabian": {"password": "1234", "role": "admin", "away": False},
    "mama":   {"password": "passwort", "role": "user", "away": False},
    "papa":   {"password": "passwort", "role": "user", "away": False},
    "laura":  {"password": "passwort", "role": "user", "away": False}
}

tasks = []
terminal_output = ["Willkommen im Terminal!"]

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    role = users[user]["role"]
    away = users[user]["away"]

    return render_template("index.html", tasks=tasks, user=user, role=role, away=away, users=users)

@app.route("/toggle_away", methods=["POST"])
def toggle_away():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    users[user]["away"] = not users[user]["away"]
    return redirect("/")

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

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in users:
            return render_template("register.html", error="Benutzername existiert bereits")

        users[username] = {"password": password, "role": "user", "away": False}
        session["user"] = username
        return redirect("/")

    return render_template("register.html")

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
# BENUTZERVERWALTUNG
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

@app.route("/admin/set_role", methods=["POST"])
def admin_set_role():
    username = request.form.get("username")
    new_role = request.form.get("role")

    if username in users:
        users[username]["role"] = new_role

    return redirect("/admin")

@app.route("/admin/toggle_away", methods=["POST"])
def admin_toggle_away():
    username = request.form.get("username")

    if username in users:
        users[username]["away"] = not users[username]["away"]

    return redirect("/admin")

@app.route("/admin/delete_user", methods=["POST"])
def admin_delete_user():
    username = request.form.get("username")

    if username in users:
        del users[username]

    return redirect("/admin")

@app.route("/admin/add_user", methods=["POST"])
def admin_add_user():
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")

    if username not in users:
        users[username] = {"password": password, "role": role, "away": False}

    return redirect("/admin")

# -------------------------
# TERMINAL
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
                        terminal_output.append(f"{username} ist jetzt NICHT im Haus")
                    elif state == "off":
                        users[username]["away"] = False
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

if __name__ == "__main__":
    app.run(debug=True)
