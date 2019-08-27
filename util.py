import datetime
import calendar

def is_time_greater(date):
    abbr_to_num = {name: num for num, name in enumerate(calendar.month_abbr) if num}
    temp_string = date[5:7] + str(abbr_to_num[date[8:11]]) + date[12:16]
    datetime_obj = datetime.datetime.strptime(temp_string, '%d%m%Y')
    datetime_now = datetime.datetime.now()

    return datetime_obj > datetime_now