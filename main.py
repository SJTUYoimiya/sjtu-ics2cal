from utils.course import *

def main():
    year = 2024
    term = 2
    course_list = get_course_list(year, term)
    courses = parse_course_list(course_list, year, term)
    cal = create_calendar(courses)
    write_calendar(cal, f'{year}-{year+1}-{term}.ics')

if __name__ == "__main__":
    main()
