## import statements
import requests_oauthlib
import webbrowser
import json
import secret_data
from datetime import datetime
import csv

## CACHING SETUP

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DEBUG = True
CACHE_FNAME = "cache_contents.json"
CREDS_CACHE_FILE = "creds.json"

# load cache_files
try:
    with open(CACHE_FNAME, 'r', encoding='utf-8') as cache_file:
        cache_json = cache_file.read()
        CACHE_DICTION = json.loads(cache_json)
except:
    CACHE_DICTION = {}

# load creds_files
try:
    with open(CREDS_CACHE_FILE, 'r', encoding='utf-8') as creds_file:
        cache_creds = creds_file.read()
        CREDS_DICTION = json.loads(cache_creds)
except:
    CREDS_DICTION = {}


# Cache functions
def has_cache_expired(timestamp_str, expire_in_days):
    """Check if cache timestamp is over expire_in_days old"""
    # gives current datetime
    now = datetime.now()

    # datetime.strptime converts a formatted string into datetime object
    cache_timestamp = datetime.strptime(timestamp_str, DATETIME_FORMAT)

    # subtracting two datetime objects gives you a timedelta object
    delta = now - cache_timestamp
    delta_in_days = delta.days

    # now that we have days as integers, we can just use comparison
    # and decide if cache has expired or not
    if delta_in_days > expire_in_days:
        return True  # It's been longer than expiry time
    else:
        return False


def get_from_cache(identifier, dictionary):
    """If unique identifier exists in specified cache dictionary and has not expired, return the data associated with it from the request, else return None"""
    identifier = identifier.upper()  # Assuming none will differ with case sensitivity here
    if identifier in dictionary:
        data_assoc_dict = dictionary[identifier]
        if has_cache_expired(data_assoc_dict['timestamp'], data_assoc_dict["expire_in_days"]):
            if DEBUG:
                print("Cache has expired for {}".format(identifier))
            # also remove old copy from cache
            del dictionary[identifier]
            data = None
        else:
            data = dictionary[identifier]['values']
    else:
        data = None
    return data


def set_in_data_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the data cache dictionary, and save the whole dictionary to a file as json"""
    identifier = identifier.upper()
    CACHE_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CACHE_FNAME, 'w', encoding='utf-8') as cache_file:
        cache_json = json.dumps(CACHE_DICTION, indent=4, sort_keys=True)
        cache_file.write(cache_json)


def set_in_creds_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the credentials cache dictionary, and save the whole dictionary to a file as json"""
    identifier = identifier.upper()  # make unique
    CREDS_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CREDS_CACHE_FILE, 'w', encoding='utf-8') as cache_file:
        cache_json = json.dumps(CREDS_DICTION, indent=4, sort_keys=True)
        cache_file.write(cache_json)


## ADDITIONAL CODE for program should go here...
## Perhaps authentication setup, functions to get and process data, a class definition... etc.

CLIENT_KEY = secret_data.client_key
CLIENT_SECRET = secret_data.client_secret

REQUEST_TOKEN_URL = 'https://www.tumblr.com/oauth/request_token'
BASE_AUTH_URL = 'https://www.tumblr.com/oauth/authorize'
ACCESS_TOKEN_URL = 'https://www.tumblr.com/oauth/access_token'


def get_tokens(client_key=CLIENT_KEY, client_secret=CLIENT_SECRET, request_token_url=REQUEST_TOKEN_URL,
               base_authorization_url=BASE_AUTH_URL, access_token_url=ACCESS_TOKEN_URL, verifier_auto=True):
    # Create an instance of the OAuth1 session class that is defined in the requests_oauthlib library, passing in the client key and client secret so that they can be used in various operations later.
    oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret)

    # Fetch Request Token to get a Key and Secret
    fetch_response = oauth_inst.fetch_request_token(request_token_url)

    # Extract OAuth/Request/Owner Token Key and OAuth/Request/Owner Token Secret
    resource_owner_key = fetch_response.get('oauth_token')
    resource_owner_secret = fetch_response.get('oauth_token_secret')

    # Create Authorization URL
    auth_url = oauth_inst.authorization_url(base_authorization_url)

    # Open the URL in browser, user gives permission
    webbrowser.open(auth_url)

    if verifier_auto:
        verifier = input('Please input the verifier: ')
    else:
        redirect_result = input("Paste the full redirect URL here:  ")
        oauth_resp = oauth_inst.parse_authorization_response(redirect_result)
        verifier = oauth_resp.get('oauth_verifier')

    # Regenerate instance of oauth1session class with more data
    oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret,
                                                 resource_owner_key=resource_owner_key,
                                                 resource_owner_secret=resource_owner_secret, verifier=verifier)

    # Fetch Access Token using ACCESS_TOKEN_URL
    oauth_tokens = oauth_inst.fetch_access_token(access_token_url)

    # Extract new OAuth/Request/Owner Token Key and OAuth/Request/Owner Token Secret
    resource_owner_key, resource_owner_secret = oauth_tokens.get('oauth_token'), oauth_tokens.get('oauth_token_secret')

    # In the end you have an oAuth1 session instance with Client Key, Client Secret, Token Key, Token Secret, Verifier
    return client_key, client_secret, resource_owner_key, resource_owner_secret, verifier


def get_tokens_from_service(service_name_ident, expire_in_days=7):  # Default: 7 days for creds expiration
    creds_data = get_from_cache(service_name_ident, CREDS_DICTION)
    if creds_data:
        if DEBUG:
            print("Loading creds from cache...")
            print()
    else:
        if DEBUG:
            print("Fetching fresh credentials...")
            print("Prepare to log in via browser.")
            print()
        creds_data = get_tokens()
        set_in_creds_cache(service_name_ident, creds_data, expire_in_days=expire_in_days)
    return creds_data


def create_request_identifier(url, params_diction):
    sorted_params = sorted(params_diction.items(), key=lambda x: x[0])
    params_str = "_".join([str(e) for l in sorted_params for e in
                           l])  # Make the list of tuples into a flat list using a complex list comprehension
    total_ident = url + "?" + params_str
    return total_ident.upper()  # Creating the identifier


def get_data_from_api(request_url, service_ident, params_diction, expire_in_days=7):
    """Check in cache, if not found, load data, save in cache and then return that data"""
    ident = create_request_identifier(request_url, params_diction)
    data = get_from_cache(ident, CACHE_DICTION)
    if data:
        if DEBUG:
            print("Loading from data cache: {}... data".format(ident))
    else:
        if DEBUG:
            print("Fetching new data from {}".format(request_url))

        # Get credentials
        client_key, client_secret, resource_owner_key, resource_owner_secret, verifier = get_tokens_from_service(
            service_ident)

        # Create a new instance of oauth to make a request with
        oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret,
                                                     resource_owner_key=resource_owner_key,
                                                     resource_owner_secret=resource_owner_secret)
        # Call the get method on oauth instance
        # Work of encoding and "signing" the request happens behind the sences, thanks to the OAuth1Session instance in oauth_inst
        resp = oauth_inst.get(request_url, params=params_diction)
        # Get the string data and set it in the cache for next time
        data_str = resp.text
        data = json.loads(data_str)
        set_in_data_cache(ident, data, expire_in_days)
    return data


class Post(object):
    def __init__(self, post_dict):
        self.title = post_dict['slug']
        self.note_count = post_dict['note_count']
        self.summary = post_dict['summary']
        self.tags = post_dict['tags']
        self.date = post_dict['date']
        self.url = post_dict['short_url']


def get_result(blog_id):
    tumblr_search_baseurl = 'https://api.tumblr.com/v2/blog/{}.tumblr.com/posts'.format(blog_id)
    tumblr_search_params = {'limit': 20}
    tumblr_result = get_data_from_api(tumblr_search_baseurl, "Tumblr", tumblr_search_params)

    post_list = []
    for post_dict in tumblr_result['response']['posts']:
        post_list.append(Post(post_dict))
    return post_list


## Make sure to run your code and write CSV files by the end of the program.
FIELD_NAMES = ['title', 'note_count', 'summary', 'tags', 'date', 'url']


def write_to_csv(blog_id, post_list):
    file_name = '{}.csv'.format(blog_id)
    with open(file_name, 'w', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, FIELD_NAMES)
        writer.writeheader()
        for post in post_list:
            writer.writerow({
                'title': post.title,
                'note_count': post.note_count,
                'summary': post.summary,
                'tags': post.tags,
                'date': post.date,
                'url': post.url
            })


def main():
    if not CLIENT_KEY or not CLIENT_SECRET:
        print("You need to fill in client_key and client_secret in the secret_data.py file.")
        exit()
    if not REQUEST_TOKEN_URL or not BASE_AUTH_URL:
        print("You need to fill in this API's specific OAuth2 URLs in this file.")
        exit()

    # invoke the functions
    post_list1 = get_result('lsleofskye')
    post_list2 = get_result('whitney-hayes')
    write_to_csv('lsleofskye', post_list1)
    write_to_csv('whitney-hayes', post_list2)


if __name__ == "__main__":
    main()
