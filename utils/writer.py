from dataclasses import dataclass
import datetime
from icalendar import Calendar, Event

from .login import Login
from .const import *

################################################################################
# crawl course list from i.sjtu.edu.cn
def get_course_list(year: int, term: int) -> list:
    print("Trying to login to i.sjtu.edu.cn...\n")
    session = Login("https://i.sjtu.edu.cn/jaccountlogin").session
    print("Login successful! Trying to get course list...\n")

    url = "https://i.sjtu.edu.cn/kbcx/xskbcx_cxXsgrkb.html?gnmkdm=N2151"
    headers = {
        'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
    }
    data = {
        'xnm': year,
        'xqm': TERM_DICT[term],
    }
    res = session.post(url, data=data, headers=headers)
    res.raise_for_status()

    if res.headers['Content-Type'].startswith('application/json'):
        res = res.json()

        if res['xsxx']['KCMS'] == 0:
            print("You have no courses in this term.")
            exit(0)
        elif res['xsxx']['KCMS'] > 0:
            return res['kbList']

################################################################################
# parse course list
@dataclass
class Course:
    name: str
    id: str
    teacher: str
    campus: str
    room: str
    weeks: tuple[tuple[int], int]
    weekday: int
    period: tuple[int]
    term_start: datetime.date

    def __post_init__(self):
        self.weekday = int(self.weekday)
        self.period = tuple(map(int, self.period.split('-')))

        weeks, interval = self.weeks.split('周')
        weeks = tuple(map(int, weeks.split('-')))

        if interval:
            interval = 2
        else:
            if len(weeks) == 1:
                interval = 0
            elif len(weeks) == 2:
                interval = 1

        self.weeks = (weeks, interval)

    def repeat_rule(self):
        weeks, interval = self.weeks
        if len(weeks) == 1:
            repeat = 1
        elif len(weeks) == 2:
            repeat = (weeks[1] - weeks[0]) // interval + 1
        
        return {'freq': 'weekly', 'interval': interval, 'count': repeat}

    def time(self):
        # Get the start and end time of the period of the course
        start_time = TIMETABLE[self.period[0]][0]
        end_time = TIMETABLE[self.period[1]][1]

        # Get the date of the course
        week = self.weeks[0][0]
        date = self.term_start + datetime.timedelta(days=self.weekday-1, weeks=week-1)

        # Concat the date and time
        start_time = datetime.datetime.combine(date, start_time)
        end_time = datetime.datetime.combine(date, end_time)
        return start_time, end_time
    
    def __repr__(self):
        return f"Course(name={self.name}, id={self.id}, teacher={self.teacher}, room={self.room}, weeks={self.weeks}, weekday={self.weekday}, period={self.period})"

def parse_course_list(course_list: list[dict], year: int, term: int):
    for course_info in course_list:
        name = course_info['kcmc']
        id = course_info['kch']
        teacher = course_info['xm']
        campus = course_info['xqmc']
        room = course_info['cdmc']
        weekday = course_info['xqj']
        period = course_info['jcs']

        week_info = course_info['zcd']
        for weeks in week_info.split(','):
            course = Course(
                name, id, teacher, campus, room, weeks, weekday, period,
                TERM_START_DATE[year][term]
            )
            yield course

################################################################################
# write course list to ics file
def create_event(course: Course):
    event = Event()
    event.add('summary', course.name)
    event.add('description', f'{course.id} {course.teacher}')
    event.add('location', f'{course.campus} {course.room}')
    event.add('dtstamp', datetime.datetime.now())
    dtstart, dtend = course.time()
    event.add('dtstart', dtstart)
    event.add('dtend', dtend)
    if course.weeks[1] > 0:
        event.add('rrule', course.repeat_rule())
    return event

def create_calendar(courses: list[Course]):
    cal = Calendar()
    cal.add('prodid', '-//My calendar product//mxm.dk//')
    cal.add('version', '2.0')
    for course in courses:
        cal.add_component(create_event(course))
    return cal

def write_calendar(cal: Calendar, filename: str = 'cal.ics'):
    with open(filename, 'wb') as f:
        f.write(cal.to_ical())
    print(f"Calendar has been written to {filename}")

if __name__ == '__main__':
    pass
