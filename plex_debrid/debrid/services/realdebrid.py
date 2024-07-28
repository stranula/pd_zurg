#import modules
from base import *
from ui.ui_print import *
import releases
import os
import csv
import pprint

# (required) Name of the Debrid service
name = "Real Debrid"
short = "RD"
# (required) Authentification of the Debrid service, can be oauth aswell. Create a setting for the required variables in the ui.settings_list. For an oauth example check the trakt authentification.
api_key = ""
# Define Variables
session = requests.Session()
errors = [
    [202," action already done"],
    [400," bad Request (see error message)"],
    [403," permission denied (infringing torrent or account locked or not premium)"],
    [503," service unavailable (see error message)"],
    [404," wrong parameter (invalid file id(s)) / unknown ressource (invalid id)"],
    ]
def setup(cls, new=False):
    from debrid.services import setup
    setup(cls,new)

# Error Log
def logerror(response):
    if not response.status_code in [200,201,204]:
        desc = ""
        for error in errors:
            if response.status_code == error[0]:
                desc = error[1]
        ui_print("[realdebrid] error: (" + str(response.status_code) + desc + ") " + str(response.content), debug=ui_settings.debug)
    if response.status_code == 401:
        ui_print("[realdebrid] error: (401 unauthorized): realdebrid api key does not seem to work. check your realdebrid settings.")
    if response.status_code == 403:
        ui_print("[realdebrid] error: (403 unauthorized): You may have attempted to add an infringing torrent or your realdebrid account is locked or you dont have premium.")

# Set the CSV file path from environment variable, default to 'catalog.csv'
CSV_FILE_PATH = '/zurg/RD/catalog.csv'

# Ensure the directory exists
def ensure_directory_exists(file_path):
    directory = os.path.dirname(file_path)
    # print(f"Checking if directory exists: {directory}")
    if directory and not os.path.exists(directory):
        # print(f"Creating directory: {directory}")
        os.makedirs(directory)
    else:
        # print(f"Directory already exists: {directory}")
        pass


# CSV Writing Function
def write_to_csv(data, torrent_file_name, actual_title):
    ensure_directory_exists(CSV_FILE_PATH)
    file_exists = os.path.isfile(CSV_FILE_PATH)
    with open(CSV_FILE_PATH, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['EID', 'Title', 'Type', 'Year', 'ParentEID', 'ParentTitle', 'ParentType', 'ParentYear', 'GrandParentEID', 'GrandParentTitle', 'GrandParentType', 'GrandParentYear', 'Torrent File Name', 'Actual Title'])  # header
        row = data + [torrent_file_name, actual_title]
        writer.writerow(row)

# Pretty-print the element object
def print_element_details(element):
    print("Element details:")
    try:
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(vars(element))
    except Exception as e:
        print(f"An error occurred while printing element details: {e}")

# Extract necessary fields from element
def extract_element_data(element):
    eid = element.EID if hasattr(element, 'EID') else ''
    title = element.title if hasattr(element, 'title') else ''
    type_ = element.type if hasattr(element, 'type') else ''
    year = element.year if hasattr(element, 'year') else ''
    parentEID = element.parentEID if hasattr(element, 'parentEID') and element.parentEID else ''
    parentTitle = element.parentTitle if hasattr(element, 'parentTitle') else ''
    parentType = element.parentType if hasattr(element, 'parentType') else ''
    parentYear = element.parentYear if hasattr(element, 'parentYear') else ''
    grandparentEID = element.grandparentEID if hasattr(element, 'grandparentEID') and element.grandparentEID else ''
    grandparentTitle = element.grandparentTitle if hasattr(element, 'grandparentTitle') else ''
    grandparentType = element.grandparentType if hasattr(element, 'grandparentType') else ''
    grandparentYear = element.grandparentYear if hasattr(element, 'grandparentYear') else ''
    
    return [eid, title, type_, year, parentEID, parentTitle, parentType, parentYear, grandparentEID, grandparentTitle, grandparentType, grandparentYear]

# Get Function
def get(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36','authorization': 'Bearer ' + api_key}
    response = None
    try:
        response = session.get(url, headers=headers)
        logerror(response)
        response = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))
    except Exception as e:
        ui_print("[realdebrid] error: (json exception): " + str(e), debug=ui_settings.debug)
        response = None
    return response

# Post Function
def post(url, data):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36','authorization': 'Bearer ' + api_key}
    response = None
    try:
        response = session.post(url, headers=headers, data=data)
        logerror(response)
        response = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))
    except Exception as e:
        if hasattr(response,"status_code"):
            if response.status_code >= 300:
                ui_print("[realdebrid] error: (json exception): " + str(e), debug=ui_settings.debug)
        else:
            ui_print("[realdebrid] error: (json exception): " + str(e), debug=ui_settings.debug)
        response = None
    return response

# Delete Function
def delete(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36','authorization': 'Bearer ' + api_key}
    try:
        requests.delete(url, headers=headers)
        # time.sleep(1)
    except Exception as e:
        ui_print("[realdebrid] error: (delete exception): " + str(e), debug=ui_settings.debug)
        None
    return None

# Object classes
class file:
    def __init__(self, id, name, size, wanted_list, unwanted_list):
        self.id = id
        self.name = name
        self.size = size / 1000000000
        self.match = ''
        wanted = False
        unwanted = False
        for key, wanted_pattern in wanted_list:
            if wanted_pattern.search(self.name):
                wanted = True
                self.match = key
                break

        if not wanted:
            for key, unwanted_pattern in unwanted_list:
                if unwanted_pattern.search(self.name) or self.name.endswith('.exe') or self.name.endswith('.txt'):
                    unwanted = True
                    break

        self.wanted = wanted
        self.unwanted = unwanted

    def __eq__(self, other):
        return self.id == other.id

class version:
    def __init__(self, files):
        self.files = files
        self.needed = 0
        self.wanted = 0
        self.unwanted = 0
        self.size = 0
        for file in self.files:
            self.size += file.size
            if file.wanted:
                self.wanted += 1
            if file.unwanted:
                self.unwanted += 1

# (required) Download Function.
def create_symlinks_from_catalog(src_dir, dest_dir, dest_dir_movies, catalog_path, processed_items_file, ignore_processed=False):
    catalog_data = read_catalog_csv(catalog_path)
    
    if ignore_processed:
        processed_items = set()
    else:
        processed_items = read_processed_items(processed_items_file)
        
    new_processed_items = set(processed_items)

    print(f"Catalog data read from {catalog_path}")

    for entry in catalog_data:
        try:
            eid = entry['EID']
            torrent_dir_name = entry['Torrent File Name']
            
            # Skip if the torrent_dir_name is in the processed items and we're not ignoring processed items
            if not ignore_processed and torrent_dir_name in processed_items:
                continue

            title = entry['Title']
            type_ = entry['Type']
            year = entry['Year']
            parent_title = entry['ParentTitle']
            parent_type = entry['ParentType']
            parent_year = entry['ParentYear']
            grandparent_title = entry['GrandParentTitle']
            grandparent_type = entry['GrandParentType']
            grandparent_year = entry['GrandParentYear']
            actual_title = entry['Actual Title']

            # Determine the correct destination directory (movies or shows)
            if type_ == 'movie':
                base_title = title
                base_year = year
                tmdb_id = extract_id(entry['EID']) if entry['EID'] else 'unknown'
                if f"({base_year})" in base_title:
                    folder_name = f"{base_title} {{tmdb-{tmdb_id}}}"
                else:
                    folder_name = f"{base_title} ({base_year}) {{tmdb-{tmdb_id}}}"
                target_folder = os.path.join(dest_dir_movies, folder_name)

                # Ensure target folder exists
                if not os.path.exists(target_folder):
                    os.makedirs(target_folder, exist_ok=True)
                    print(f"Created target folder: {target_folder}")

                torrent_dir_path = find_best_match(torrent_dir_name, actual_title, src_dir)
                if not torrent_dir_path:
                    print(f"No matching directory found for {torrent_dir_name} or {actual_title}")
                    continue
                print(f"Processing torrent directory: {torrent_dir_path}")

                # Find the largest file in the movie folder
                largest_file = None
                largest_size = 0
                for file_name in os.listdir(torrent_dir_path):
                    file_path = os.path.join(torrent_dir_path, file_name)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        if file_size > largest_size:
                            largest_size = file_size
                            largest_file = file_name

                if largest_file:
                    file_ext = os.path.splitext(largest_file)[1]
                    resolution = extract_resolution(largest_file, parent_folder_name=torrent_dir_path, file_path=os.path.join(torrent_dir_path, largest_file))
                    target_file_name = f"{base_title}  ({base_year}) {{tmdb-{tmdb_id}}} [{resolution}]{file_ext}"
                    target_file_name = clean_filename(target_file_name)
                    target_file_path = os.path.join(target_folder, target_file_name)
                    
                    largest_file_path = os.path.join(torrent_dir_path, largest_file)
                    if not os.path.exists(target_file_path):
                        try:
                            # Create relative symlink
                            relative_source_path = os.path.relpath(largest_file_path, os.path.dirname(target_file_path))
                            os.symlink(relative_source_path, target_file_path)
                            print(f"Created relative symlink: {target_file_path} -> {relative_source_path}")
                        except OSError as e:
                            print(f"Error creating relative symlink: {e}")
                    else:
                        print(f"Symlink already exists: {target_file_path}")

            else:
                # TV show handling code
                base_title = grandparent_title if grandparent_title else parent_title if parent_title else title
                base_year = grandparent_year if grandparent_year else parent_year if parent_year else year
                tmdb_id = extract_id(entry.get('GrandParentEID')) if entry.get('GrandParentEID') else extract_id(entry.get('ParentEID')) if entry.get('ParentEID') else extract_id(entry.get('EID')) if entry.get('EID') else 'unknown'

                if f"({base_year})" in base_title:
                    folder_name = f"{base_title} {{tmdb-{tmdb_id}}}"
                else:
                    folder_name = f"{base_title} ({base_year}) {{tmdb-{tmdb_id}}}"
                target_folder = os.path.join(dest_dir, folder_name)

                if not os.path.exists(target_folder):
                    try:
                        os.makedirs(target_folder)
                        print(f"Created target folder: {target_folder}")
                    except OSError as e:
                        print(f"Error creating target folder: {e}")
                        continue

                torrent_dir_path = find_best_match(torrent_dir_name, actual_title, src_dir)
                if not torrent_dir_path:
                    print(f"No matching directory found for {torrent_dir_name} or {actual_title}")
                    continue
                print(f"Processing torrent directory: {torrent_dir_path}")

                for file_name in os.listdir(torrent_dir_path):
                    file_path = os.path.join(torrent_dir_path, file_name)
                    print(f"Processing file: {file_path}")

                    if os.path.isfile(file_path):
                        file_ext = os.path.splitext(file_name)[1]

                        season, episode = extract_season_episode(file_name)
                        if not (season and episode):
                            print(f"Skipping file (no season/episode info): {file_name}")
                            continue

                        season_folder = f"Season {season}"
                        episode_identifier = f"S{season}E{episode}"

                        resolution = extract_resolution(file_name, parent_folder_name=torrent_dir_path, file_path=file_path)
                        target_file_name = f"{base_title} ({base_year}) {{tmdb-{tmdb_id}}} - {episode_identifier} [{resolution}]{file_ext}"

                        target_folder_season = os.path.join(target_folder, season_folder)
                        if not os.path.exists(target_folder_season):
                            os.makedirs(target_folder_season, exist_ok=True)

                        target_file_path = os.path.join(target_folder_season, target_file_name)
                        target_file_name = clean_filename(target_file_name)

                        if not os.path.exists(file_path):
                            print(f"Source file does not exist: {file_path}")
                        elif not os.path.exists(target_file_path):
                            try:
                                # Create relative symlink
                                relative_source_path = os.path.relpath(file_path, os.path.dirname(target_file_path))
                                os.symlink(relative_source_path, target_file_path)
                                print(f"Created relative symlink: {target_file_path} -> {relative_source_path}")
                            except OSError as e:
                                print(f"Error creating relative symlink: {e}")
                        else:
                            print(f"Symlink already exists: {target_file_path}")

            new_processed_items.add(torrent_dir_name)
        except Exception as e:
            print(f"Error processing entry: {e}")

    write_processed_items(processed_items_file, new_processed_items)

# (required) Check Function
def check(element, force=False):
    if force:
        wanted = ['.*']
    else:
        wanted = element.files()
    unwanted = releases.sort.unwanted
    wanted_patterns = list(zip(wanted, [regex.compile(r'(' + key + ')', regex.IGNORECASE) for key in wanted]))
    unwanted_patterns = list(zip(unwanted, [regex.compile(r'(' + key + ')', regex.IGNORECASE) for key in unwanted]))

    hashes = []
    for release in element.Releases[:]:
        if len(release.hash) == 40:
            hashes += [release.hash]
        else:
            ui_print("[realdebrid] error (missing torrent hash): ignoring release '" + release.title + "' ",ui_settings.debug)
            element.Releases.remove(release)
    if len(hashes) > 0:
        response = get('https://api.real-debrid.com/rest/1.0/torrents/instantAvailability/' + '/'.join(hashes))
        ui_print("[realdebrid] checking and sorting all release files ...", ui_settings.debug)
        for release in element.Releases:
            release.files = []
            release_hash = release.hash.lower()
            if hasattr(response, release_hash):
                response_attr = getattr(response, release_hash)
                if hasattr(response_attr, 'rd'):
                    rd_attr = response_attr.rd
                    if len(rd_attr) > 0:
                        for cashed_version in rd_attr:
                            version_files = []
                            for file_ in cashed_version.__dict__:
                                file_attr = getattr(cashed_version, file_)
                                debrid_file = file(file_, file_attr.filename, file_attr.filesize, wanted_patterns, unwanted_patterns)
                                version_files.append(debrid_file)
                            release.files += [version(version_files), ]
                        # select cached version that has the most needed, most wanted, least unwanted files and most files overall
                        release.files.sort(key=lambda x: len(x.files), reverse=True)
                        release.files.sort(key=lambda x: x.wanted, reverse=True)
                        release.files.sort(key=lambda x: x.unwanted, reverse=False)
                        release.wanted = release.files[0].wanted
                        release.unwanted = release.files[0].unwanted
                        release.size = release.files[0].size
                        release.cached += ['RD']
                        continue
        ui_print("done",ui_settings.debug)
