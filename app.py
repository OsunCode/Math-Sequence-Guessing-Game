from flask import Flask, jsonify, render_template, request
from game_engine import GameManager
from database import Database
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-for-production")

db = Database(os.path.join(BASE_DIR, "game_history.db"))
games = GameManager(db)

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/api/games")
def start_game():
    data = request.get_json(silent=True) or {}
    try:
        result = games.start(
            sequence_type=data.get("sequence_type", ""),
            num_questions=data.get("num_questions"),
            time_limit=data.get("time_limit"),
            base=data.get("base")
        )
        return jsonify(result), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

@app.get("/api/games/<game_id>")
def game_status(game_id):
    try:
        return jsonify(games.status(game_id))
    except KeyError:
        return jsonify({"error": "Game not found."}), 404

@app.post("/api/games/<game_id>/answers")
def submit_answer(game_id):
    data = request.get_json(silent=True) or {}
    try:
        result = games.answer(game_id, data.get("answer"))
        return jsonify(result)
    except KeyError:
        return jsonify({"error": "Game not found."}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

@app.post("/api/games/<game_id>/abandon")
def abandon_game(game_id):
    try:
        return jsonify(games.abandon(game_id))
    except KeyError:
        return jsonify({"error": "Game not found."}), 404

@app.get("/api/history")
def history():
    try:
        limit = min(max(int(request.args.get("limit", 50)), 1), 200)
    except ValueError:
        limit = 50
    return jsonify({"games": db.get_history(limit)})

@app.get("/api/statistics")
def statistics():
    return jsonify(db.get_statistics())

@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False, threaded=True)
