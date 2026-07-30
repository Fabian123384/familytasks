import webview
import threading
import app  # deine Flask-App

def start_flask():
    app.app.run()

# Flask in einem eigenen Thread starten
threading.Thread(target=start_flask).start()

# Desktop-Fenster öffnen
webview.create_window("Familien Aufgaben App", "http://127.0.0.1:5000")
webview.start()
