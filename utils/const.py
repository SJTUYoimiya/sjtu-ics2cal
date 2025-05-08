import datetime

TIMETABLE = {
    1: (datetime.time(8, 0), datetime.time(8, 45)),
    2: (datetime.time(8, 55), datetime.time(9, 40)),
    3: (datetime.time(10, 0), datetime.time(10, 45)),
    4: (datetime.time(10, 55), datetime.time(11, 40)),
    5: (datetime.time(12, 0), datetime.time(12, 45)),
    6: (datetime.time(12, 55), datetime.time(13, 40)),
    7: (datetime.time(14, 0), datetime.time(14, 45)),
    8: (datetime.time(14, 55), datetime.time(15, 40)),
    9: (datetime.time(16, 0), datetime.time(16, 45)),
    10: (datetime.time(16, 55), datetime.time(17, 40)),
    11: (datetime.time(18, 0), datetime.time(18, 45)),
    12: (datetime.time(18, 55), datetime.time(19, 40)),
    13: (datetime.time(19, 35), datetime.time(20, 20)),
}

TERM_START_DATE = {
    2021: {
        1: datetime.date(2021, 9, 13),
        2: datetime.date(2022, 2, 14),
        3: datetime.date(2022, 6, 20)
    },
    2022: {
        1: datetime.date(2022, 9, 12),
        2: datetime.date(2023, 2, 13),
        3: datetime.date(2025, 6, 19)
    },
    2023: {
        1: datetime.date(2023, 9, 11),
        2: datetime.date(2025, 2, 19),
        3: datetime.date(2025, 6, 24)
    },
    2024: {
        1: datetime.date(2024, 9, 16),
        2: datetime.date(2025, 2, 17),
        3: datetime.date(2025, 6, 23)
    },
}

TERM_DICT = {
    1: '3',
    2: '12',
    3: '16'
}