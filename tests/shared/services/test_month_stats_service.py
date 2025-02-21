from datetime import datetime
import unittest
from unittest.mock import patch
import src.shared.database.sqlite_db as sqlite_db
from src.web_api.services.stats_service import MonthStatService


class TestMonthStatService(unittest.TestCase):
    def setUp(self):
        self.connexion = sqlite_db.connect(":memory:")
        sqlite_db.create_tables(self.connexion)
        self.connexion.execute(
            "INSERT INTO tasks (task_name, guid) VALUES ('Test', '1234')"
        )
        self.connexion.execute(
            """INSERT INTO timer_data (date, task_id, time_beginning, time_ending, time_elapsed, guid)
                                    VALUES ('2024-01-01', '1', '12:00:00', '12:05:00', '300', '1234'),
                                            ('2024-01-08', '1', '12:00:00', '12:05:00', '300', '2234'),
                                            (strftime('%Y-%m-%d', 'now'), '1', '12:00:00', '12:05:00', '300', '3234');
                                """
        )
        self.connexion.commit()


    def tearDown(self):
        self.connexion.close()


    def test_month_weeks_columns(self):
        result = MonthStatService(self.connexion).get_column_dates("2025-01-01")
        self.assertEqual(len(result), 5)


    def test_month_generic_stats_when_first_week_is_zero(self):
        self.connexion.execute("""INSERT INTO timer_data (date, task_id, time_beginning, time_ending, time_elapsed, guid)
                                    VALUES ('2025-01-01', '1', '12:00:00', '12:05:00', '300', '1345'),
                                            ('2025-01-08', '1', '12:00:00', '12:05:00', '300', '2345'),
                                            ('2025-01-15', '1', '12:00:00', '12:05:00', '300', '3345'),
                                            ('2025-01-22', '1', '12:00:00', '12:05:00', '300', '4345'),
                                            ('2025-01-29', '1', '12:00:00', '12:05:00', '300', '5345'),
                                            ('2025-01-31', '1', '12:00:00', '12:05:00', '300', '6345');
                                """)
        result = MonthStatService(self.connexion).get_generic_stat("2025-01-01")
        self.assertEqual(result,
                        {'weeks': ['01', '02', '03', '04', '05'],
                         'stackedBarChart': [{'name': 'Test', 'data': [100.0, 100.0, 100.0, 100.0, 100.0]}],
                         'weeksLineChart': {'name': 'Total time', 'data': [300.0, 300.0, 300.0, 300.0, 600.0]}
                        }
                        )


    def test_month_generic_stats_with_multiple_tasks(self):
        self.connexion.execute("""INSERT INTO tasks (id, task_name, guid) VALUES (2, 'Test2', '4567');""")
        self.connexion.execute("""INSERT INTO timer_data (date, task_id, time_beginning, time_ending, time_elapsed, guid)
                                    VALUES ('2025-01-01', '1', '12:00:00', '12:05:00', '300', '1345'),
                                            ('2025-01-08', '1', '12:00:00', '12:05:00', '300', '2345'),
                                            ('2025-01-15', '1', '12:00:00', '12:05:00', '300', '3345'),
                                            ('2025-01-22', '1', '12:00:00', '12:05:00', '300', '4345'),
                                            ('2025-01-29', '1', '12:00:00', '12:05:00', '300', '5345'),
                                            ('2025-01-31', '2', '12:00:00', '12:05:00', '300', '6345');
                                """)
        result = MonthStatService(self.connexion).get_generic_stat("2025-01-01")
        # Checking there are as much labels as tasks
        self.assertEqual(len(result["stackedBarChart"]), 2)
        # Checking that ratio for last week is correctly split
        self.assertEqual(result["stackedBarChart"][0]["data"][-1], 50)


    def test_month_generic_stats_line_chart(self):
        self.connexion.execute("""INSERT INTO timer_data (date, task_id, time_beginning, time_ending, time_elapsed, guid)
                                VALUES ('2025-01-31', '1', '12:00:00', '12:05:00', '300', '6345');""")
        result = MonthStatService(self.connexion).get_generic_stat("2025-01")
        self.assertEqual(
            result,
            {
                "weeks": ["01", "02", "03", "04", "05"],
                "stackedBarChart": [{"name": "Test", "data": [0, 0, 0, 0, 100.0]}],
                "weeksLineChart": {"name": "Total time", "data": [0, 0, 0, 0, 300.0]},
            },
        )
    

    def test_line_chart_is_none_next_week(self):
        with patch('tests.shared.services.test_month_stats_service.datetime') as mock_date:
            mock_date.now.return_value = datetime(2025, 2, 21)
            mock_date.side_effect = lambda *args, **kw: datetime(*args, **kw)

            self.connexion.execute("""INSERT INTO timer_data (date, task_id, time_beginning, time_ending, time_elapsed, guid)
                            VALUES ('2025-02-01', '1', '12:00:00', '12:05:00', '300', '1345'),
                                    ('2025-02-08', '1', '12:00:00', '12:05:00', '300', '2345'),
                                    ('2025-02-15', '1', '12:00:00', '12:05:00', '300', '3345')
                        """)
            result = MonthStatService(self.connexion).get_generic_stat()
            self.assertEqual(result["weeksLineChart"]["data"], [300.0, 300.0, 300.0, 0, None])

if __name__ == '__main__':
    unittest.main()
