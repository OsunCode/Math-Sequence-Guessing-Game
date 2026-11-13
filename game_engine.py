import time
import uuid
import threading

class GameManager:
    """In-memory active sessions; completed games are persisted in SQLite."""

    def __init__(self, database):
        self.database = database
        self.active_games = {}
        self.lock = threading.RLock()

    @staticmethod
    def _positive_int(value, label, maximum):
        try:
            number = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{label} must be a whole number.")
        if number <= 0:
            raise ValueError(f"{label} must be greater than zero.")
        if number > maximum:
            raise ValueError(f"{label} cannot exceed {maximum}.")
        return number

    def start(self, sequence_type, num_questions, time_limit, base=None):
        sequence_type = str(sequence_type).strip().lower()
        if sequence_type not in ("fibonacci", "powers"):
            raise ValueError("Choose Fibonacci or Powers.")
        count = self._positive_int(num_questions, "Number of questions", 100)
        seconds = self._positive_int(time_limit, "Time limit", 3600)
        parsed_base = None
        if sequence_type == "powers":
            parsed_base = self._positive_int(base, "Base", 1000)

        game_id = str(uuid.uuid4())
        game = {
            "id": game_id,
            "sequence_type": sequence_type,
            "num_questions": count,
            "time_limit": seconds,
            "base": parsed_base,
            "started_at": time.time(),
            "question_index": 0,
            "correct": 0,
            "incorrect": 0,
            "answers": [],
            "sequence": [0, 1] if sequence_type == "fibonacci" else [],
            "finished": False,
            "saved": False,
        }
        with self.lock:
            self.active_games[game_id] = game
        return self._payload(game, message="Game started.")

    def _question(self, game):
        index = game["question_index"]
        if game["sequence_type"] == "fibonacci":
            sequence = game["sequence"]
            expected = sequence[-1] + sequence[-2]
            prompt = "What number comes next?"
            hint = "Continue the Fibonacci sequence."
            display = list(sequence)
        else:
            expected = game["base"] ** index
            prompt = f"What is {game['base']} to the power of {index}?"
            hint = "Remember: any nonzero number to the zero power equals 1."
            display = list(game["sequence"])
        return {
            "question_number": index + 1,
            "prompt": prompt,
            "hint": hint,
            "sequence": display,
            "expected": expected,
        }

    def _remaining(self, game):
        elapsed = max(0, time.time() - game["started_at"])
        return max(0, game["time_limit"] - elapsed)

    def _finish(self, game, reason):
        if not game["finished"]:
            game["finished"] = True
            game["finish_reason"] = reason
            game["finished_at"] = time.time()
        if not game["saved"]:
            elapsed = max(0, game.get("finished_at", time.time()) - game["started_at"])
            skipped = max(0, game["num_questions"] - len(game["answers"]))
            self.database.save_game({
                "id": game["id"],
                "sequence_type": game["sequence_type"],
                "base": game["base"],
                "num_questions": game["num_questions"],
                "correct": game["correct"],
                "incorrect": game["incorrect"],
                "skipped": skipped,
                "accuracy": round(game["correct"] / game["num_questions"] * 100, 2),
                "elapsed_seconds": round(elapsed, 2),
                "finish_reason": game.get("finish_reason", reason),
            })
            game["saved"] = True

    def _payload(self, game, message=None, last_result=None):
        remaining = self._remaining(game)
        if not game["finished"] and remaining <= 0:
            self._finish(game, "time")
        completed = game["finished"]
        result = {
            "game_id": game["id"],
            "sequence_type": game["sequence_type"],
            "base": game["base"],
            "num_questions": game["num_questions"],
            "question_index": game["question_index"],
            "correct": game["correct"],
            "incorrect": game["incorrect"],
            "answered": len(game["answers"]),
            "skipped": max(0, game["num_questions"] - len(game["answers"])) if completed else 0,
            "remaining_seconds": round(self._remaining(game), 1),
            "finished": completed,
            "finish_reason": game.get("finish_reason"),
            "message": message,
            "last_result": last_result,
        }
        if completed:
            result["summary"] = {
                "correct": game["correct"],
                "incorrect": game["incorrect"],
                "skipped": max(0, game["num_questions"] - len(game["answers"])),
                "total": game["num_questions"],
                "accuracy": round(game["correct"] / game["num_questions"] * 100, 2),
                "elapsed_seconds": round(game.get("finished_at", time.time()) - game["started_at"], 2),
            }
        else:
            result["question"] = self._question(game)
        return result

    def status(self, game_id):
        with self.lock:
            game = self.active_games.get(game_id)
            if not game:
                raise KeyError(game_id)
            return self._payload(game)

    def abandon(self, game_id):
        with self.lock:
            game = self.active_games.get(game_id)
            if not game:
                raise KeyError(game_id)
            self._finish(game, "abandoned")
            return self._payload(game, message="Game ended early.")

    def answer(self, game_id, answer):
        try:
            submitted = int(str(answer).strip())
        except (TypeError, ValueError):
            raise ValueError("Enter a whole number.")
        with self.lock:
            game = self.active_games.get(game_id)
            if not game:
                raise KeyError(game_id)
            if game["finished"]:
                return self._payload(game, message="This game has already finished.")
            if self._remaining(game) <= 0:
                self._finish(game, "time")
                return self._payload(game, message="Time is up.")

            question = self._question(game)
            expected = question["expected"]
            is_correct = submitted == expected
            if is_correct:
                game["correct"] += 1
            else:
                game["incorrect"] += 1

            game["answers"].append({
                "submitted": submitted,
                "expected": expected,
                "correct": is_correct,
            })
            # Advance the sequence even after an incorrect answer.
            game["sequence"].append(expected)
            game["question_index"] += 1
            last_result = {
                "correct": is_correct,
                "submitted": submitted,
                "expected": expected,
            }

            if game["question_index"] >= game["num_questions"]:
                self._finish(game, "completed")
                return self._payload(game, message="All questions completed.", last_result=last_result)
            return self._payload(game, message="Answer recorded.", last_result=last_result)
