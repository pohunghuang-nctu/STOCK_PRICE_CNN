#!/home/user/anaconda3/bin/python
from datetime import date, datetime, timedelta

def nextday(date_str):
    d = datetime.strptime(date_str, '%Y_%m_%d')
    return (d + timedelta(days=1)).strftime('%Y_%m_%d')


def y_m_d(day_str):
    return int(day_str[:4]), int(day_str[5:7]), int(day_str[8:])


def day_next_month(day_str):
    y, m, d = y_m_d(day_str)
    if m == 12:
        y += 1
        m = 1
    else:
        if m == 1 and d in [29, 30, 31]:
            if y % 4 == 0:
                d = 29
            else:
                d = 28
        elif m in [3, 5, 8, 10] and d == 31:
            d = 30
        m += 1
    return '%d_%02d_%02d' % (y, m, d)


def day_prev_month(day_str):
    y, m, d = y_m_d(day_str)
    if m == 1:
        y -= 1
        m = 12
    else:
        if m == 3 and d in [29, 30, 31]:
            if y % 4 == 0:
                d = 29
            else:
                d = 28
        elif m in [5, 7, 10, 12] and d == 31:
            d = 30
        m -= 1
    return '%d_%02d_%02d' % (y, m, d)


def day_next3_year(day_str):
    y, m, d = y_m_d(day_str)
    if m == 2 and d == 29:
        d = 28
    y += 3
    return '%d_%02d_%02d' % (y, m, d)


def date_to_week(day_str):
    dt = datetime.strptime(day_str, '%Y_%m_%d')
    week_str = dt.strftime('%Y_%W')
    return week_str

def week_prev_year(day_str):
    y, m, d = y_m_d(day_str)
    if m == 2 and d == 29:
        d = 28
    y -= 1
    d = datetime.strptime('%d_%02d_%02d' % (y, m, d), '%Y_%m_%d')
    return d.strftime('%Y_%W')
