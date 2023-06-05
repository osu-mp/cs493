activities = "activities"
child = "child"
date = "date"
users = "users"

date_test = "date_test"     # key for the hardcoded date string when in test mode
date_format = "%Y-%m-%d"    # format that birthdays are expected to be formatted int
debug_date = "2023-06-05"
# monthlty
age_groups = [2, 4, 6, 8, 9, 10, 12, 14, 16, 18, 20, 22, 24, 27, 30, 33, 36, 42, 48, 54, 60]
max_age = 66

min_name_length = 2
min_premature_weeks = 0
max_premature_weeks = 40
provider_code_length = 6

pagination_query_limit = 5

# Global flag for debugging. Set to False before deployment
DEBUG = True


# local version
url_root = "http://127.0.0.1:8080"
# deployed version
# url_root = "https://hw9-paceym.wm.r.appspot.com"

