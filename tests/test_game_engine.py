import os
import tempfile
import unittest
from database import Database
from game_engine import GameManager

class GameEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)
        self.manager = GameManager(self.db)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_fibonacci_first_question_and_scoring(self):
        game = self.manager.start("fibonacci", 2, 30)
        game_id = game["game_id"]
        self.assertEqual(game["question"]["sequence"], [0, 1])
        first = self.manager.answer(game_id, 1)
        self.assertTrue(first["last_result"]["correct"])
        second = self.manager.answer(game_id, 4)
        self.assertTrue(second["finished"])
        self.assertEqual(second["summary"]["correct"], 1)
        self.assertEqual(second["summary"]["incorrect"], 1)
        self.assertEqual(second["summary"]["accuracy"], 50.0)

    def test_powers_starts_at_zero_exponent(self):
        game = self.manager.start("powers", 1, 30, 3)
        result = self.manager.answer(game["game_id"], 1)
        self.assertTrue(result["finished"])
        self.assertTrue(result["last_result"]["correct"])

    def test_invalid_game_settings(self):
        with self.assertRaises(ValueError):
            self.manager.start("unknown", 5, 30)
        with self.assertRaises(ValueError):
            self.manager.start("fibonacci", 0, 30)

if __name__ == "__main__":
    unittest.main()
