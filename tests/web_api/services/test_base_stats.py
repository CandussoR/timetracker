from datetime import datetime
import unittest
from unittest.mock import patch

import src.shared.database.sqlite_db as sqlite_db
from src.web_api.services.stats_service import StatServiceFactory
from werkzeug.datastructures import ImmutableMultiDict

class TestStats(unittest.TestCase):
    week_return = [{'task': 'Test', 'time': 300.0, 'formatted': ['00', '05', '00'], 'ratio': 50.0},
                   {'task': 'Test2', 'time': 300.0, 'formatted': ['00', '05', '00'], 'ratio': 50.0}]
    year_and_month_return = [{'task': 'Test', 'time': 600.0, 'formatted': ['00', '10', '00'], 'ratio': 66.7},
            {'task': 'Test2', 'time': 300.0, 'formatted': ['00', '05', '00'], 'ratio': 33.3}]
    def setUp(self):
        self.connexion = sqlite_db.connect(":memory:")
        sqlite_db.create_tables(self.connexion)
        self.connexion.execute(
            "INSERT INTO tasks (task_name, guid) VALUES ('Test', '1234'), ('Test2', '4556')"
        )
        self.connexion.execute(
            """INSERT INTO timer_data (date, task_id, time_beginning, time_ending, time_elapsed, guid)
                                    VALUES ('2025-01-01', '1', '12:00:00', '12:05:00', '300', '1234'),
                                            ('2025-01-02', '2','12:00:00', '12:05:00', '300', '1235'), 
                                            ('2025-01-08', '1', '12:00:00', '12:05:00', '300', '2234')
                                """
        )
        self.connexion.commit()


    def tearDown(self):
        self.connexion.close()

    # Tests for the refactoring
    def test_task_time_ratio_week_with_date(self):
        service = StatServiceFactory().create_stat_service(self.connexion, ImmutableMultiDict([('period', 'week'), ('date', '2025-01-01')]))
        ret = service.get_task_time_ratio()
        self.assertEqual(ret, self.week_return)
    
    def test_task_time_ratio_day_with_date(self):
        service = StatServiceFactory().create_stat_service(self.connexion, ImmutableMultiDict([('period', 'day'), ('date', '2025-01-01')]))
        ret = service.get_task_time_ratio()
        ret_due = [{'task': 'Test', 'time': 300.0, 'formatted': ['00', '05', '00'], 'ratio': 100.0}]
        self.assertEqual(ret, ret_due)

    def test_task_time_ratio_month_with_date(self):
        service = StatServiceFactory().create_stat_service(self.connexion, ImmutableMultiDict([('period', 'month'), ('date', '2025-01')]))
        ret = service.get_task_time_ratio()
        self.assertEqual(ret, self.year_and_month_return)

    def test_task_time_ratio_year_with_date(self):
        service = StatServiceFactory().create_stat_service(self.connexion, ImmutableMultiDict([('period', 'year'), ('date', '2025')]))
        ret = service.get_task_time_ratio()
        self.assertEqual(ret, self.year_and_month_return)
    
    def test_task_time_ratio_day_without_date(self):
        with patch('src.web_api.services.stats_service.datetime') as mock_date:
            mock_date.now.return_value = datetime(2025, 1, 1)
            mock_date.side_effect = lambda *args, **kw: datetime(*args, **kw)

            service = StatServiceFactory().create_stat_service(self.connexion, ImmutableMultiDict([('period', 'day')]))
            ret = service.get_task_time_ratio()
            ret_due = [{'task': 'Test', 'time': 300.0, 'formatted': ['00', '05', '00'], 'ratio': 100.0}]
            self.assertEqual(ret, ret_due)
        
    def test_task_time_ratio_week_without_date(self):
        with patch('src.web_api.services.stats_service.datetime') as mock_date:
            mock_date.now.return_value = datetime(2025, 1, 1)
            mock_date.side_effect = lambda *args, **kw: datetime(*args, **kw)

            service = StatServiceFactory().create_stat_service(self.connexion, ImmutableMultiDict([('period', 'week')]))
            ret = service.get_task_time_ratio()
            self.assertEqual(ret, self.week_return)
    
    def test_task_time_ratio_month_without_date(self):
        with patch('src.web_api.services.stats_service.datetime') as mock_date:
            mock_date.now.return_value = datetime(2025, 1, 1)
            mock_date.side_effect = lambda *args, **kw: datetime(*args, **kw)

            service = StatServiceFactory().create_stat_service(self.connexion, ImmutableMultiDict([('period', 'month')]))
            ret = service.get_task_time_ratio()
            self.assertEqual(ret, self.year_and_month_return)
    
    def test_task_time_ratio_year_without_date(self):
        with patch('tests.shared.services.test_base_stats.datetime') as mock_date:
            mock_date.now.return_value = datetime(2025, 12, 31)
            mock_date.side_effect = lambda *args, **kw: datetime(*args, **kw)

            service = StatServiceFactory().create_stat_service(self.connexion, ImmutableMultiDict([('period', 'year')]))
            ret = service.get_task_time_ratio()
            self.assertEqual(ret, self.year_and_month_return)

if __name__ == '__main__':
    unittest.main()
