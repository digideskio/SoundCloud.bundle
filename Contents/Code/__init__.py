NAME = "SoundCloud"
CLIENT_ID = "4f6c5882fe9cfc80ebf7ff815cd8b383"

TRACKS_URL = 'http://api.soundcloud.com/tracks.json?client_id=%s&filter=streamable&offset=%d&limit=30'
USERS_URL = 'http://api.soundcloud.com/users.json?client_id=%s&q=%s&offset=%d&limit=30'
USERS_TRACKS_URL = 'http://api.soundcloud.com/users/%s/tracks.json?client_id=%s&offset=%d&limit=30'
FAVORITES_URL = 'http://api.soundcloud.com/users/%s/favorites.json?client_id=%s&offset=%d&limit=30'
GROUPS_URL = 'http://api.soundcloud.com/groups.json?client_id=%s&q=%s&offset=%d&limit=30'
GROUPS_TRACKS_URL = 'http://api.soundcloud.com/groups/%s/tracks.json?client_id=%s&offset=%d&limit=30'

####################################################################################################
def Start():

    ObjectContainer.title1 = NAME

####################################################################################################
@handler('/music/soundcloud', NAME)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Hot', params = {'order': 'hotness'}), title = 'Hot'))
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Latest', params = {'order': 'created_at'}), title = 'Latest'))
    oc.add(InputDirectoryObject(key = Callback(Search), title = "Tracks Search...", prompt = "Search for Tracks"))
    oc.add(InputDirectoryObject(key = Callback(UsersSearch), title = "Users Search...", prompt = "Search for Users"))
    oc.add(InputDirectoryObject(key = Callback(GroupsSearch), title = "Groups Search...", prompt = "Search for Groups"))
    return oc

####################################################################################################
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
def UserOptions(user):

    oc = ObjectContainer(title2 = '')

    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Favorites', params = {}, id = user['id'], type = "favs"), title = 'Favorites'))
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Tracks', params = {}, id = user['id'], type = "user"), title = 'Tracks'))

    return oc

####################################################################################################
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

        # Construct a list of thumbnails, in expected size order, largest first
        thumb = ''
        if track['artwork_url'] != None:
            original_thumb = track['artwork_url']
            ordered_thumbs = [original_thumb.replace('large', 'original'),
                              original_thumb.replace('large', 't500x500'),
                              original_thumb]
            thumb = ordered_thumbs

        oc.add(TrackObject(
            url = track['stream_url'],
            title = track['title'],
            thumb = Resource.ContentsOfURLWithFallback(thumb),
            duration = int(track['duration'])
        ))

    # Allow the user to move to the next page...
    if len(request) == 30:
        oc.add(NextPageObject(key = Callback(ProcessRequest, title = title, params = params, offset = offset + 25, id = id, type = type), title = 'Next...'))

    return oc
