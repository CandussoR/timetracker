from datetime import datetime
import sqlite3
import unittest
from unittest.mock import patch

import src.shared.database.sqlite_db as sqlite_db
from src.web_api.services.stats_service import YearStatService
from werkzeug.datastructures import ImmutableMultiDict

class TestYearStatService(unittest.TestCase):
    def setUp(self):
        self.connexion = sqlite_db.connect(':memory:')
        sqlite_db.create_tables(self.connexion)
        self.connexion.execute("INSERT INTO tasks (task_name, guid) VALUES ('Test', '1234')")
        self.connexion.execute('''INSERT INTO timer_data (date, task_id, time_beginning, time_ending, time_elapsed, guid)
                                    VALUES ('2024-01-01', '1', '12:00:00', '12:05:00', '300', '1234'),
                                            ('2024-01-08', '1', '12:00:00', '12:05:00', '300', '2234'),
                                            (strftime('%Y-%m-%d', 'now'), '1', '12:00:00', '12:05:00', '300', '3234'); ''')
        self.connexion.commit()


    def tearDown(self):
        self.connexion.close()

    
    def test_get_year_generic_stats(self):
        result = YearStatService(self.connexion).get_generic_stat("2024")
        self.assertNotEqual(result["details"]["months"], [])
        self.assertNotEqual(result["details"]["stackedBarChart"], [])
        self.assertNotEqual(result["details"]["monthsLineChart"], [])
        self.assertNotEqual(result["details"]["weekLineChart"], [])

    
    def test_get_total_time_per_week_for_years(self):
        self.connexion.execute('''INSERT INTO timer_data (date, task_id, time_beginning, time_ending, time_elapsed, guid)
                            VALUES ('2025-01-01', '1', '12:00:00', '12:05:00', '300', '1334'),
                                    ('2025-01-08', '1', '12:00:00', '12:05:00', '300', '2334'),
                                    (strftime('%Y-%m-%d', 'now'), '1', '12:00:00', '12:05:00', '300', '3334'); ''')
        # Year beginning by week 01 in sqlite
        result1 = YearStatService(self.connexion).get_total_time_per_week_for_year("2024")
        self.assertEqual(result1["2024"][0]["x"], 1)
        # Year beginning by week 00 in sqlite
        result = YearStatService(self.connexion).get_total_time_per_week_for_year("2025")
        # Is this one ajusted ?
        self.assertEqual(result["2025"][0]["x"], 1)


if __name__ == '__main__':
    unittest.main()