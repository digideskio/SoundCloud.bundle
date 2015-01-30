NAME = "SoundCloud"
CLIENT_ID = "7c2d3445e3bef47d9ddbbe02d859c5f3"
CLIENT_SECRET = "a2f4e60c71bbcd324c4c7432fe56809d"

TRACKS_URL = 'http://api.soundcloud.com/tracks.json?client_id=%s&filter=streamable&offset=%d&limit=30'
USERS_URL = 'http://api.soundcloud.com/users.json?client_id=%s&q=%s&offset=%d&limit=30'
USERS_TRACKS_URL = 'http://api.soundcloud.com/users/%s/tracks.json?client_id=%s&offset=%d&limit=30'
FAVORITES_URL = 'http://api.soundcloud.com/users/%s/favorites.json?client_id=%s&offset=%d&limit=30'
GROUPS_URL = 'http://api.soundcloud.com/groups.json?client_id=%s&q=%s&offset=%d&limit=30'
GROUPS_TRACKS_URL = 'http://api.soundcloud.com/groups/%s/tracks.json?client_id=%s&offset=%d&limit=30'
MY_STREAM_URL = 'https://api.soundcloud.com/me/activities/tracks.json?limit=30&oauth_token=%s'
MY_TRACKS_URL = 'https://api.soundcloud.com/me/tracks.json?&offset=%d&limit=30&oauth_token=%s'
MY_FAVORITES_URL = 'https://api.soundcloud.com/me/favorites.json?&offset=%d&limit=30&oauth_token=%s'

####################################################################################################
def Start():

    ObjectContainer.title1 = NAME
    Dict.Reset()
    Authenticate()

####################################################################################################
def ValidatePrefs():
    Authenticate()

####################################################################################################
@handler('/music/soundcloud', NAME)
def MainMenu():

    oc = ObjectContainer(no_cache = True)
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Hot', params = {'order': 'hotness'}), title = 'Hot'))
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Latest', params = {'order': 'created_at'}), title = 'Latest'))
    oc.add(InputDirectoryObject(key = Callback(Search), title = "Tracks Search...", prompt = "Search for Tracks"))
    oc.add(InputDirectoryObject(key = Callback(UsersSearch), title = "Users Search...", prompt = "Search for Users"))
    oc.add(InputDirectoryObject(key = Callback(GroupsSearch), title = "Groups Search...", prompt = "Search for Groups"))
    oc.add(PrefsObject(title="Preferences"))
    oc.add(DirectoryObject(key = Callback(MyAccount), title = "My Account"))
    return oc


####################################################################################################
@route('/music/soundcloud/my-account')
def MyAccount():
    if Prefs['username'] and Prefs['password']:
        Authenticate()
    else:
        return ObjectContainer(header="Login", message="Enter your username and password in Preferences")

    if 'loggedIn' in Dict and Dict['loggedIn'] == True:
        oc = ObjectContainer(title2="My Account")
        oc.add(DirectoryObject(key = Callback(MyStream), title='My Stream'))
        oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'My Tracks', params = {'order': 'created_at'}, type = "my-tracks"), title = 'My Tracks'))
        oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'My Favorites', params = {}, type = "my-favs"), title = 'My Favorites'))
        return oc
    else:
        return ObjectContainer(header="Login Failed", message="Please check your username and password")

####################################################################################################
def Authenticate():
    Log.Debug("Authenticate")
    if Prefs['username'] and Prefs['password']:
        try:
            #curl --data "grant_type=password&client_id=7c2d3445e3bef47d9ddbbe02d859c5f3&client_secret=a2f4e60c71bbcd324c4c7432fe56809d&username=<USERNAME>&password=<PASSWORD>&scope=non-expiring" https://api.soundcloud.com/oauth2/token

            Log.Debug("Attempting soundcloud authentication")
            auth = JSON.ObjectFromURL('https://api.soundcloud.com/oauth2/token', values=dict(
                grant_type='password',
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                username=Prefs['username'],
                password=Prefs['password'],
                scope='non-expiring'))
            Dict['loggedIn'] = True
            Log.Info("Login Successful")
            Dict['access_token'] = auth['access_token'];
            return True
        except Ex.HTTPError, e:
            Log.Error(e.content)
            Dict['loggedIn'] = False
            Log.Error('Login Failed')
            return False
        except:
            Dict['loggedIn'] = False
            Log.Error('Login Failed')
            return False
    else:
        return False

####################################################################################################
@route('/music/soundcloud/my-stream')
def MyStream(url = ''):
    if not Dict['loggedIn']:
        return ObjectContainer(header="Login", message="Enter your username and password in Preferences")

    token = (Dict['access_token'])
    if url == '':
        request_url = MY_STREAM_URL % token
    else:
        request_url = url.replace("/tracks?", "/tracks.json?") + "&oauth_token=" + token

    response = JSON.ObjectFromURL(request_url)
    collection = response['collection']
    
    oc = ObjectContainer(title2 = 'My Stream')
    for activity in collection:
        origin = activity['origin']
        if not origin['streamable']:
            continue
        AddTrack(oc, origin)
    
    if 'next_href' in response:
        next_href = response['next_href']
        oc.add(NextPageObject(key = Callback(MyStream, url = next_href), title = 'Next...'))

    return oc

####################################################################################################
@route('/music/soundcloud/search/groups', offset = int, allow_sync = True)
def GroupsSearch(query = '', offset = 0):

    oc = ObjectContainer(title2 = query)
    
    # Construct a suitable user URL request...
    request_url = GROUPS_URL % (CLIENT_ID, String.Quote(query, usePlus=True), offset)
    request = JSON.ObjectFromURL(request_url, cacheTime = 0)

    if 'errors' in request and len(request['errors'] > 0) and len(request) == 1:
        return ObjectContainer(header="Error", message="There are no available items...")

    for group in request:

        # Construct a list of thumbnails, in expected size order, largest first
        thumb = ''
        if group['artwork_url'] != None:
            original_thumb = group['artwork_url']
            ordered_thumbs = [original_thumb.replace('large', 'original'),
                              original_thumb.replace('large', 't500x500'),
                              original_thumb]
            thumb = ordered_thumbs

        oc.add(DirectoryObject(key = Callback(ProcessRequest, title = group['name'], params = {}, id = group['id'], type = "group"), title = group['name'], thumb = Resource.ContentsOfURLWithFallback(thumb)))

    # Allow the user to move to the next page...
    if len(request) == 30:
        oc.add(NextPageObject(key = Callback(GroupsSearch, query = query, offset = offset + 25), title = 'Next...'))

    return oc

####################################################################################################
@route('/music/soundcloud/search/users', offset = int, allow_sync = True)
def UsersSearch(query = '', offset = 0):

    oc = ObjectContainer(title2 = query)

    # Construct a suitable user URL request...
    request_url = USERS_URL % (CLIENT_ID, String.Quote(query, usePlus=True), offset)
    request = JSON.ObjectFromURL(request_url, cacheTime = 0)

    if 'errors' in request and len(request['errors'] > 0) and len(request) == 1:
        return ObjectContainer(header="Error", message="There are no available items...")

    for user in request:

        # Construct a list of thumbnails, in expected size order, largest first
        thumb = ''
        if user['avatar_url'] != None:
            original_thumb = user['avatar_url']
            ordered_thumbs = [original_thumb.replace('large', 'original'),
                              original_thumb.replace('large', 't500x500'),
                              original_thumb]
            thumb = ordered_thumbs

        oc.add(DirectoryObject(key = Callback(UserOptions, user = user), title = user['username'], thumb = Resource.ContentsOfURLWithFallback(thumb)))
        #oc.add(DirectoryObject(key = Callback(ProcessRequest, title = user['username'], params = {}, id = user['id'], type = "favs"), title = user['username'], thumb = thumb))

    # Allow the user to move to the next page...
    if len(request) == 30:
        oc.add(NextPageObject(key = Callback(UsersSearch, query = query, offset = offset + 25), title = 'Next...'))

    return oc

####################################################################################################
@route('/music/soundcloud/user/{user}')
def UserOptions(user):

    oc = ObjectContainer(title2 = '')

    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Favorites', params = {}, id = user['id'], type = "favs"), title = 'Favorites'))
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Tracks', params = {}, id = user['id'], type = "user"), title = 'Tracks'))

    return oc

####################################################################################################
@route('/music/soundcloud/search', allow_sync = True)
def Search(query = 'music'):

    return ProcessRequest(title = query, params = {'q': query})

####################################################################################################
@route('/music/soundcloud/{title}', params = dict, offset = int, allow_sync = True)
def ProcessRequest(title, params, offset = 0, id = -1, type = "default"):

    oc = ObjectContainer(title2 = title)

    if type == 'default':
        # Construct a suitable track URL request...
        request_url = TRACKS_URL % (CLIENT_ID, offset)
        for param, value in params.items():
            request_url = request_url + ('&%s=%s' % (param, String.Quote(value, usePlus=True)))
    elif type == 'user':
        request_url = USERS_TRACKS_URL % (id, CLIENT_ID, offset)
    elif type == 'favs':
        request_url = FAVORITES_URL % (id, CLIENT_ID, offset)
    elif type == 'group':
        request_url = GROUPS_TRACKS_URL % (id, CLIENT_ID, offset)
    elif type == 'my-tracks':
        request_url = MY_TRACKS_URL % (offset, Dict['access_token'])
    elif type == 'my-favs':
        request_url = MY_FAVORITES_URL % (offset, Dict['access_token'])

    request = JSON.ObjectFromURL(request_url, cacheTime = 0)

    # It's possible that the request has caused an error to occur. This is easily producible, e.g. if
    # the user searches for something like 'the'. Unfortunately, the API doesn't give us any way to 
    # detect this, except for a single 503 - Service Unavailable erro. This can be seen in the following
    # url: http://api.soundcloud.com/tracks.json?client_id=4f6c5882fe9cfc80ebf7ff815cd8b383&q=the
    if 'errors' in request and len(request['errors'] > 0) and len(request) == 1:
        return ObjectContainer(header="Error", message="There are no available items...")

    for track in request:

        # For some reason, although we've asked for only 'streamable' content, we still sometimes find
        # items which do not have a stream_url. We need to catch these and simply ignore them...
        if track['streamable'] == False:
            continue

        AddTrack(oc, track)


    # Allow the user to move to the next page...
    if len(request) == 30:
        oc.add(NextPageObject(key = Callback(ProcessRequest, title = title, params = params, offset = offset + 25, id = id, type = type), title = 'Next...'))

    return oc

####################################################################################################
def AddTrack(oc, track):
    # Construct a list of thumbnails, in expected size order, largest first
    thumb = ''
    if track['artwork_url'] != None:
        original_thumb = track['artwork_url']
        ordered_thumbs = [original_thumb.replace('large', 'original'),
                          original_thumb.replace('large', 't500x500'),
                          original_thumb]
        thumb = ordered_thumbs
    
    if track['user'] != None:
        artist = track['user']['username']
    else:
        artist = '[Unknown]'

    oc.add(TrackObject(
        url = track['stream_url'],
        title = track['title'],
        thumb = Resource.ContentsOfURLWithFallback(thumb),
        duration = int(track['duration']),
        artist = artist,
        source_title = 'SoundCloud'
    ))
