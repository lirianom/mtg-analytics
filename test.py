import datetime
import calendar

bearertoken_time = 'Wed, 19 Jun 2019 00:58:35 GMT'

testString = bearertoken_time[5:16]
abbr_to_num = {name: num for num, name in enumerate(calendar.month_abbr) if num}
testString = bearertoken_time[5:7] + str(abbr_to_num[bearertoken_time[8:11]]) + bearertoken_time[12:16]
datetime_obj = datetime.datetime.strptime(testString, '%d%m%Y')
datetime_now = datetime.datetime.now()

print(datetime_obj > datetime_now)
