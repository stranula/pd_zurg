from base import *

import content
import scraper
import releases
import debrid
from ui import ui_settings
from ui.ui_print import *
from settings import *

#import uvicorn

config_dir = ""
service_mode = False

class option:
    def __init__(self, name, cls, key):
        self.name = name
        self.cls = cls
        self.key = key

    def input(self):
        func = getattr(self.cls, self.key)
        func()

def ignored():
    back = False
    while not back:
        ui_cls('Options/Ignored Media/')
        if len(content.classes.ignore.ignored) == 0:
            library = content.classes.library()[0]()
            if len(library) > 0:
                # get entire plex_watchlist
                plex_watchlist = content.services.plex.watchlist()
                # get entire trakt_watchlist
                trakt_watchlist = content.services.trakt.watchlist()
                print('checking new content ...')
                for iterator in itertools.zip_longest(plex_watchlist, trakt_watchlist):
                    for element in iterator:
                        if hasattr(element, 'uncollected') and hasattr(element, 'watched'):
                            element.watched()
                            element.uncollected(library)
            print()
        print('0) Back')
        indices = []
        for index, element in enumerate(content.classes.ignore.ignored):
            print(str(index + 1) + ') ' + element.query())
            indices += [str(index + 1)]
        print()
        choice = input('Choose a media item that you want to remove from the ignored list: ')
        if choice in indices:
            print("Media item: " + content.classes.ignore.ignored[int(choice) - 1].query() + ' removed from ignored list.')
            content.classes.ignore.ignored[int(choice) - 1].unwatch()
            time.sleep(3)
        elif choice == '0':
            back = True
    options()

def scrape():
    ui_cls('Options/Scraper/')
    print('Press Enter to return to the main menu.')
    print()
    print("Please choose a version to scrape for: ")
    print()
    obj = releases.release('', '', '', [], 0, [])
    indices = []
    for index, version in enumerate(releases.sort.versions):
        print(str(index + 1) + ') ' + version[0] + (' (disabled)' if '\u0336' in version[0] else ''))
        indices += [str(index + 1)]
    print(str(index + 2) + ') Scrape without defining a version')
    indices += [str(index + 2)]
    print()
    choice = input("Choose a version: ")
    if choice in indices and not choice == str(index + 2):
        obj.version = releases.sort.version(releases.sort.versions[int(choice) - 1][0],
                                            releases.sort.versions[int(choice) - 1][1],
                                            releases.sort.versions[int(choice) - 1][2],
                                            releases.sort.versions[int(choice) - 1][3])
    elif choice == str(index + 2):
        obj.version = None
    else:
        return
    while True:
        ui_cls('Options/Scraper/')
        print('Press Enter to return to the main menu.')
        print()
        query = input("Enter a query: ")
        if query == '':
            return
        print()
        if hasattr(obj,"version"):
            if not obj.version == None:
                for trigger, operator, value in obj.version.triggers:
                    if trigger == "scraper sources":
                        if operator in ["==","include"]:
                            if value in scraper.services.active:
                                scraper.services.overwrite += [value]
                        elif operator == "exclude":
                            if value in scraper.services.active:
                                for s in scraper.services.active:
                                    if not s == value:
                                        scraper.services.overwrite += [s]
                    if trigger == "scraping adjustment":
                        if operator == "add text before title":
                            query = value + query
                        elif operator == "add text after title":
                            query = query + value
        scraped_releases = scraper.scrape(query)
        if len(scraped_releases) > 0:
            obj.Releases = scraped_releases
            debrid.check(obj, force=True)
            scraped_releases = obj.Releases
            if not obj.version == None:
                releases.sort(scraped_releases, obj.version)
            back = False
            while not back:
                ui_cls('Options/Scraper/')
                print("0) Back")
                releases.print_releases(scraped_releases)
                print()
                print("Type 'auto' to automatically download the first cached release.")
                print()
                choice = input("Choose a release to download: ")
                try:
                    if choice == 'auto':
                        release = scraped_releases[0]
                        release.Releases = scraped_releases
                        release.type = ("show" if regex.search(r'(S[0-9]+|SEASON|E[0-9]+|EPISODE|[0-9]+-[0-9])',release.title,regex.I) else "movie")
                        if debrid.download(release, stream=True, query=query, force=True):
                            content.classes.media.collect(release)
                            scraped_releases.remove(scraped_releases[0])
                            time.sleep(3)
                        else:
                            print()
                            print("These releases do not seem to be cached on your debrid services. Add uncached torrent?")
                            print()
                            print("0) Back")
                            print("1) Add uncached torrent")
                            print()
                            choice = input("Choose an action: ")
                            if choice == '1':
                                debrid.download(release, stream=False, query=query, force=True)
                                content.classes.media.collect(release)
                                scraped_releases.remove(scraped_releases[0])
                                time.sleep(3)
                    elif int(choice) <= len(scraped_releases) and not int(choice) <= 0:
                        release = scraped_releases[int(choice) - 1]
                        release.Releases = [release, ]
                        release.type = ("show" if regex.search(r'(S[0-9]+|SEASON|E[0-9]+|EPISODE|[0-9]+-[0-9])',release.title,regex.I) else "movie")
                        if debrid.download(release, stream=True, query=release.title, force=True):
                            content.classes.media.collect(release)
                            scraped_releases.remove(scraped_releases[int(choice) - 1])
                            time.sleep(3)
                        else:
                            print()
                            print(
                                "This release does not seem to be cached on your debrid services. Add uncached torrent?")
                            print()
                            print("0) Back")
                            print("1) Add uncached torrent")
                            print()
                            choice2 = input("Choose an action: ")
                            if choice2 == '1':
                                if debrid.download(release, stream=False, query=query, force=True):
                                    content.classes.media.collect(release)
                                    scraped_releases.remove(scraped_releases[int(choice) - 1])
                                    time.sleep(3)
                                else:
                                    print()
                                    print(
                                        "There was an error adding this uncached torrent to your debrid service. Choose another release?")
                    elif choice == '0':
                        back = True
                except:
                    back = False
        else:
            print("No releases were found!")
            time.sleep(3)

def settings():
    back = False
    while not back:
        list = settings_list
        ui_cls('Options/Settings/')
        print('0) Back')
        indices = []
        for index, category in enumerate(list):
            print(str(index + 1) + ') ' + category[0])
            indices += [str(index + 1)]
        print()
        print('Type "discard" to go back and discard changes.')
        print()
        choice = input('Choose an action: ')
        if choice in indices:
            ui_cls('Options/Settings/' + list[int(choice) - 1][0] + '/')
            settings = []
            for index, setting in enumerate(list[int(choice) - 1][1]):
                if not setting.hidden:
                    settings += [setting]
            if len(settings) > 1:
                print('0) Back')
                for index, setting in enumerate(settings):
                    if not setting.hidden:
                        print(str(index + 1) + ') ' + setting.name)
                print()
                choice2 = input('Choose an action: ')
            else:
                choice2 = '1'
            for index, setting in enumerate(list[int(choice) - 1][1]):
                if choice2 == str(index + 1) and not setting.hidden:
                    ui_cls('Options/Settings/' + list[int(choice) - 1][0] + '/' + setting.name)
                    setting.input()
        elif choice == '0':
            save()
            back = True
        elif choice == 'discard':
            load(doprint=True)
            back = True

def options():
    current_module = sys.modules[__name__]
    list = [
        option('Run', current_module, 'download_script_run'),
        option('Settings', current_module, 'settings'),
        option('Ignored Media', current_module, 'ignored'),
        option('Scraper', current_module, 'scrape'),
    ]
    ui_cls('Options/',update=update_available())
    for index, option_ in enumerate(list):
        print(str(index + 1) + ') ' + option_.name)
    print()
    print('Type exit to quit.')
    print()
    choice = input('Choose an action: ')
    if choice == 'exit':
        exit()
    for index, option_ in enumerate(list):
        if choice == str(index + 1):
            option_.input()
    options()

def setup():
    if os.path.exists(config_dir + '/settings.json'):
        if os.path.getsize(config_dir + '/settings.json') > 0 and os.path.isfile(config_dir + '/settings.json'):
            with open(config_dir + '/settings.json', 'r') as f:
                settings = json.loads(f.read())
            if settings['Show Menu on Startup'] == "false" or service_mode == True:
                return False
            load()
            return True
    ui_cls('Initial Setup')
    try:
        input('Press Enter to continue: ')
    except:
        print("Error: It seems this terminal is not interactive! Please make sure to allow user input in this terminal. For docker, add the 'interactive' flag ('-ti').")
        time.sleep(10)
        exit()
    for category, settings in settings_list:
        for setting in settings:
            if setting.required:
                ui_cls('Options/Settings/' + category + '/' + setting.name)
                setting.setup()
    ui_cls('Done!')
    input('Press Enter to continue to the main menu: ')
    save()
    return True

def save(doprint=True):
    save_settings = {}
    for category, settings in settings_list:
        for setting in settings:
            save_settings[setting.name] = setting.get()
    try:
        with open(config_dir + '/settings.json', 'w') as f:
            json.dump(save_settings, f, indent=4)
        if doprint:
            print('Current settings saved!')
            time.sleep(2)
    except:
        print()
        print("Error: It looks like plex_debrid can not write your settings into a config file. Make sure you are running the script with write or administator privilege.")
        print()
        input("Press enter to exit: ")
        exit()

def load(doprint=False, updated=False):
    with open(config_dir + '/settings.json', 'r') as f:
        settings = json.loads(f.read())
    if 'version' not in settings:
        update(settings, ui_settings.version)
        updated = True
    elif not settings['version'][0] == ui_settings.version[0] and not ui_settings.version[2] == []:
        update(settings, ui_settings.version)
        updated = True
    #compatability code for updating from <2.10 
    if 'Library Service' in settings: 
        settings['Library collection service'] = settings['Library Service']
        if settings['Library Service'] == ["Plex Library"]:
            if 'Plex \"movies\" library' in settings and 'Plex \"shows\" library' in settings: 
                settings['Plex library refresh'] = [settings['Plex \"movies\" library'],settings['Plex \"shows\" library']]
            settings['Library update services'] = ["Plex Libraries"]
        elif settings['Library Service'] == ["Trakt Collection"]:
            settings['Library update services'] = ["Trakt Collection"]
            settings['Trakt refresh user'] = settings['Trakt library user']
    #compatability code for updating from <2.20
    if not 'Library ignore services' in settings: 
        if settings['Library collection service'] == ["Plex Library"]:
            settings['Library ignore services'] = ["Plex Discover Watch Status"]
            settings["Plex ignore user"] = settings["Plex users"][0][0]
        elif settings['Library collection service'] == ["Trakt Collection"]:
            settings['Library ignore services'] = ["Trakt Watch Status"]
            settings["Trakt ignore user"] = settings["Trakt users"][0]
    for category, load_settings in settings_list:
        for setting in load_settings:
            if setting.name in settings and not setting.name == 'version' and not setting.name == 'Content Services':
                setting.set(settings[setting.name])
    if doprint:
        print('Last settings loaded!')
        time.sleep(2)
    save(doprint=updated)

def preflight():
    missing = []
    for category, settings in settings_list:
        for setting in settings:
            if setting.preflight:
                if len(setting.get()) == 0:
                    missing += [setting]
    if len(missing) > 0:
        print()
        print('Looks like your current settings didnt pass preflight checks. Please edit the following setting/s: ')
        for setting in missing:
            print(setting.name + ': Please add at least one ' + setting.entry + '.')
        print()
        input('Press Enter to return to the main menu: ')
        return False
    return True

def run(cdir = "", smode = False):
    global config_dir
    global service_mode
    config_dir = cdir
    service_mode = smode
    set_log_dir(config_dir)
    if setup():
        #uvicorn.run("webui:app", port=8008, reload=True)
        options()
    else:
        load()
        #uvicorn.run("webui:app", port=8008, reload=True)
        download_script_run()
        options()

def update_available():
    try:
        response = requests.get('https://raw.githubusercontent.com/itsToggle/plex_debrid/main/ui/ui_settings.py',timeout=0.25)
        response = response.content.decode()
        if regex.search(r"(?<=')([0-9]+\.[0-9]+)(?=')", response):
            v = regex.search(r"(?<=')([0-9]+\.[0-9]+)(?=')", response).group()
            if float(ui_settings.version[0]) < float(v):
                return " | [v"+v+"] available!"
            return ""
        return ""
    except:
        return ""

def update(settings, version):
    ui_cls('/Update ' + version[0] + '/')
    print('There has been an update to plex_debrid, which is not compatible with your current settings:')
    print()
    print(version[1])
    print()
    print('This update will overwrite the following setting/s: ' + str(version[2]))
    print('A backup file (old.json) with your old settings will be created.')
    print()
    input('Press Enter to update your settings:')
    with open(config_dir + "/old.json", "w+") as f:
        json.dump(settings, f, indent=4)
    for category, load_settings in settings_list:
        for setting in load_settings:
            for setting_name in version[2]:
                if setting.name == setting_name:
                    settings[setting.name] = setting.get()
                elif setting.name == 'version':
                    settings[setting.name] = setting.get()

def unique(lst):
    unique_objects = []
    for obj in lst:
        is_unique = True
        for unique_obj in unique_objects:
            if unique_obj == obj:
                is_unique = False
                break
        if is_unique:
            unique_objects.append(obj)
    return unique_objects

def threaded(stop):
    ui_cls()
    if service_mode == True:
        print("Running in service mode, user input not supported.")
    else:
        print("Type 'exit' to return to the main menu.")
    timeout = 5
    regular_check = 1800
    timeout_counter = 0
    library = content.classes.library()[0]()
    # get entire plex_watchlist
    plex_watchlist = content.services.plex.watchlist()
    # get entire trakt_watchlist
    trakt_watchlist = content.services.trakt.watchlist()
    # get all overseerr request
    overseerr_requests = content.services.overseerr.requests()
    # combine all content, sort by newest
    watchlists = plex_watchlist + trakt_watchlist + overseerr_requests
    try:
        watchlists.data.sort(key=lambda s: s.watchlistedAt,reverse=True)
    except:
        ui_print("couldnt sort monitored media by newest, using default order.", ui_settings.debug)
    if len(library) > 0:
        ui_print('checking new content ...')
        t0 = time.time()
        for element in unique(watchlists):
            if hasattr(element, 'download'):
                element.download(library=library)
                t1 = time.time()
                #if more than 5 seconds have passed, check for newly watchlisted content
                if t1-t0 >= 5:
                    if plex_watchlist.update() or overseerr_requests.update() or trakt_watchlist.update():
                        library = content.classes.library()[0]()
                        if len(library) == 0:
                            continue
                        new_watchlists = plex_watchlist + trakt_watchlist + overseerr_requests
                        try:
                            new_watchlists.data.sort(key=lambda s: s.watchlistedAt,reverse=True)
                        except:
                            ui_print("couldnt sort monitored media by newest, using default order.", ui_settings.debug)
                        new_watchlists = unique(new_watchlists)
                        for element in new_watchlists[:]:
                            if element in watchlists:
                                new_watchlists.remove(element)
                        ui_print('checking new content ...')
                        for element in new_watchlists:
                            if hasattr(element, 'download'):
                                element.download(library=library)
                        ui_print('done')
                    t0 = time.time()
        ui_print('done')
    while not stop():
        if plex_watchlist.update() or overseerr_requests.update() or trakt_watchlist.update():
            library = content.classes.library()[0]()
            if len(library) == 0:
                continue
            watchlists = plex_watchlist + trakt_watchlist + overseerr_requests
            try:
                watchlists.data.sort(key=lambda s: s.watchlistedAt,reverse=True)
            except:
                ui_print("couldnt sort monitored media by newest, using default order.", ui_settings.debug)
            ui_print('checking new content ...')
            for element in unique(watchlists):
                if hasattr(element, 'download'):
                    newly_added = True
                    if element.type == "show":
                        for season in element.Seasons:
                            if season in content.classes.media.ignore_queue or not newly_added:
                                newly_added = False
                                break
                            for episode in season.Episodes:
                                if episode in content.classes.media.ignore_queue:
                                    newly_added = False
                                    break
                    if newly_added:
                        element.download(library=library)
            ui_print('done')
        elif timeout_counter >= regular_check:
            # get entire plex_watchlist
            plex_watchlist = content.services.plex.watchlist()
            # get entire trakt_watchlist
            trakt_watchlist = content.services.trakt.watchlist()
            # get all overseerr request, match content to plex media type and add to monitored list
            overseerr_requests = content.services.overseerr.requests()
            # combine all content, sort by newest
            watchlists = plex_watchlist + trakt_watchlist + overseerr_requests
            try:
                watchlists.data.sort(key=lambda s: s.watchlistedAt,reverse=True)
            except:
                ui_print("couldnt sort monitored media by newest, using default order.", ui_settings.debug)
            library = content.classes.library()[0]()
            timeout_counter = 0
            if len(library) == 0:
                continue
            ui_print('checking new content ...')
            t0 = time.time()
            for element in unique(watchlists):
                if hasattr(element, 'download'):
                    element.download(library=library)
                    t1 = time.time()
                    #if more than 5 seconds have passed, check for newly watchlisted content
                    if t1-t0 >= 5:
                        if plex_watchlist.update() or overseerr_requests.update() or trakt_watchlist.update():
                            library = content.classes.library()[0]()
                            if len(library) == 0:
                                continue
                            new_watchlists = plex_watchlist + trakt_watchlist + overseerr_requests
                            try:
                                new_watchlists.data.sort(key=lambda s: s.watchlistedAt,reverse=True)
                            except:
                                ui_print("couldnt sort monitored media by newest, using default order.", ui_settings.debug)
                            new_watchlists = unique(new_watchlists)
                            for element in new_watchlists[:]:
                                if element in watchlists:
                                    new_watchlists.remove(element)
                            ui_print('checking new content ...')
                            for element in new_watchlists:
                                if hasattr(element, 'download'):
                                    element.download(library=library)
                            ui_print('done')
                        t0 = time.time()
            ui_print('done')
        else:
            timeout_counter += timeout
        time.sleep(timeout)

def download_script_run():
    if preflight():
        global stop
        stop = False
        t = Thread(target=threaded, args=(lambda: stop,))
        t.start()
        if service_mode == True:
            print("Running in service mode, user input not supported.")
        else:
            while not stop:
                text = input("")
                if text == 'exit':
                    stop = True
                else:
                    print("Type 'exit' to return to the main menu.")
        print("Waiting for the download automation to stop ... ")
        while t.is_alive():
            time.sleep(1)
