# entity names in google datastore
activities = "activities"
child = "child"
date = "date"
users = "users"

date_test = "date_test"     # key for the hardcoded date string when in test mode
date_format = "%Y-%m-%d"    # format that birthdays are expected to be formatted int
debug_date = "2023-06-05"   # when DEBUG is set to True, this is the date used as 'now'
                            # this allows for tests to calculate each child's age consistently
# monthly cut-offs for each ASQ age group
age_groups = [2, 4, 6, 8, 9, 10, 12, 14, 16, 18, 20, 22, 24, 27, 30, 33, 36, 42, 48, 54, 60]
max_age = 66                # max age (in months) a child can be used in the app

min_name_length = 2         # a child's name must be at least this many characters long
min_premature_weeks = 0     # range of acceptable premature week values
max_premature_weeks = 40
provider_code_length = 6    # expected length of code from provider for each child

pagination_query_limit = 5  # max number of entries to show in paginated GETs

# Global flag for debugging. Set to False before deployment
DEBUG = True

# local version
# url_root = "http://127.0.0.1:8080"
# deployed version
url_root = "https://hw9-paceym.wm.r.appspot.com"
