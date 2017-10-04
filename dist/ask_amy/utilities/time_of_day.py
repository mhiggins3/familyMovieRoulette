from datetime import datetime, timedelta
import re
import logging

try:
    import pytz
except ImportError:
    pass # don't freak if pytz is not installed


logger = logging.getLogger()


class TimeOfDay(object):
    Breakfast, Lunch, Dinner, Daytime, Nighttime = range(5)

    @staticmethod
    def current_time(time_adj, now=datetime.utcnow()):
        """
        current time with an offset applied
        :param time_adj: a positive or negative int to offset current time
        :param now: current time or passed time used for testing
        :return: a str version of time showing hours:minutes and am pm
        """
        if time_adj is None:
            return None

        now += timedelta(hours=int(time_adj))
        return now.strftime('%I:%M %p')

    @staticmethod
    def meal_time(time_adj, now=datetime.utcnow()):
        """
        Calculate if its breakfast, lunch or dinner time after applying and hours offset
        :param time_adj:
        :param now: current time or passed time used for testing
        :return: Breakfast, Lunch, Dinner enumeration
        """
        if time_adj is None:
            return None
        now += timedelta(hours=int(time_adj))
        # now = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")
        today430am = now.replace(hour=4, minute=30, second=0, microsecond=0)
        today1130 = now.replace(hour=11, minute=30, second=0, microsecond=0)
        today430pm = now.replace(hour=12 + 4, minute=30, second=0, microsecond=0)
        if today430am < now < today1130:
            return 'breakfast'
        elif today1130 < now < today430pm:
            return 'lunch'
        else:
            return 'dinner'

    @staticmethod
    def day_night(time_adj, now=datetime.utcnow()):
        """
        Calculate if it Daytime or Nighttime after applying and hours offset
        :param time_adj:
        :param now: current time or passed time used for testing
        :return:
        """
        if time_adj is None:
            return None
        now += timedelta(hours=int(time_adj))
        # now = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")
        today5am = now.replace(hour=5, minute=0, second=0, microsecond=0)
        today8pm = now.replace(hour=12 + 8, minute=0, second=0, microsecond=0)
        if today5am < now < today8pm:
            return 'day'
        else:
            return 'night'

    @staticmethod
    def time_adj(time_str, time_am_pm, now=datetime.utcnow()):
        """
        Given a time calculate how many hours different it is from the current system time
        :param time_str: HH:MM
        :param time_am_pm: AM or PM
        :param now: current time or passed time used for testing
        :return: int value positive or negative hours different from now()
        """
        logger.debug("**************** entering TimeOfDay.time_adj")
        if time_str is None:
            return None
        if time_am_pm is None:
            return None
        hours, minutes = time_str.split(':')
        if hours != "12" and time_am_pm.lower() == "pm":
            am_pm_shift = 12
        elif hours == "12" and time_am_pm.lower() != "pm":
            am_pm_shift = -12
        else:
            am_pm_shift = 0
        time_difference_in_hours = None
        pattern = re.compile("^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$")
        if pattern.match(time_str):
            server_time = now
            users_time = server_time.replace(hour=int(hours)+am_pm_shift, minute=int(minutes), second=0, microsecond=0)
            time_difference = users_time - server_time
            time_difference_in_hours = int(round(time_difference / timedelta(minutes=60), 0))
        return time_difference_in_hours

    @staticmethod
    def time_adj_given_tz(time_zone, now=datetime.utcnow()):

        utc = pytz.timezone('UTC')
        utc_date = utc.localize(now)

        # us_tz_nms =['US/Alaska', 'US/Hawaii', 'US/Arizona', 'US/Pacific', 'US/Mountain', 'US/Central', 'US/Eastern']

        pytz_timezone = pytz.timezone(time_zone)
        adjusted_date = utc_date.astimezone(pytz_timezone)
        # todo I'm certain there is a better way to do this (but limited on time)
        adjusted_date_str = adjusted_date.strftime("%a %b %d %H:%M:%S %Y")
        # new adjusted date is tz naive so I can subtract
        adjusted_date = adjusted_date.strptime(adjusted_date_str, "%a %b %d %H:%M:%S %Y")

        time_difference = adjusted_date - now
        time_difference_in_hours = int(round(time_difference / timedelta(minutes=60), 0))
        return time_difference_in_hours


