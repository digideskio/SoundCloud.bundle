NAME = "SoundCloud"
ART = 'art-default.jpg'
ICON = 'icon-default.png'
ICON_SEARCH = 'icon-search.png'

API_HOST = "api.soundcloud.com"
CLIENT_ID = "4f6c5882fe9cfc80ebf7ff815cd8b383"
CLIENT_SECRET = "b17b970b7a0db3729a1965d2a902efd0"

TRACKS_URL = 'http://api.soundcloud.com/tracks.json?client_id=%s&filter=streamable&offset=%d&limit=30'
USERS_URL = 'http://api.soundcloud.com/users.json?client_id=%s&q=%s&offset=%d&limit=30'
USERS_TRACKS_URL = 'http://api.soundcloud.com/users/%s/tracks.json?client_id=%s&offset=%d&limit=30'
FAVORITES_URL = 'http://api.soundcloud.com/users/%s/favorites.json?client_id=%s&offset=%d&limit=30'
GROUPS_URL = 'http://api.soundcloud.com/groups.json?client_id=%s&q=%s&offset=%d&limit=30'
GROUPS_TRACKS_URL = 'http://api.soundcloud.com/groups/%s/tracks.json?client_id=%s&offset=%d&limit=30'

####################################################################################################

# This function is initially called by the PMS framework to initialize the plugin. This includes
# setting up the Plugin static instance along with the displayed artwork.
def Start():

    # Initialize the plugin
    Plugin.AddViewGroup("List", viewMode = "List", mediaType = "items")
    Plugin.AddViewGroup("InfoList", viewMode = "InfoList", mediaType = "items")

    # Setup the artwork associated with the plugin
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    ObjectContainer.view_group = "List"

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    TrackObject.thumb = R(ICON)

####################################################################################################

@handler('/music/soundcloud', NAME, thumb = ICON, art = ART)
def MainMenu():

    oc = ObjectContainer(title1 = NAME)
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Hot', params = {'order': 'hotness'}), title = 'Hot'))
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Latest', params = {'order': 'created_at'}), title = 'Latest'))
    oc.add(InputDirectoryObject(key = Callback(Search), title = "Tracks Search...", prompt = "Search for Tracks", thumb = R(ICON_SEARCH)))
    oc.add(InputDirectoryObject(key = Callback(UsersSearch), title = "Users Search...", prompt = "Search for Users", thumb = R(ICON_SEARCH)))
    oc.add(InputDirectoryObject(key = Callback(GroupsSearch), title = "Groups Search...", prompt = "Search for Groups", thumb = R(ICON_SEARCH)))
    return oc

####################################################################################################

def GroupsSearch(query = '', offset = 0):
    oc = ObjectContainer(view_group = "InfoList", title2 = query)
    
    # Construct a suitable user URL request...
    request_url = GROUPS_URL % (CLIENT_ID, query, offset)
    request = JSON.ObjectFromURL(request_url, cacheTime = 0)
    
    if 'errors' in request and len(request['errors'] > 0) and len(request) == 1:
        return MessageContainer("Error", "There are no available items...")
        
    for group in request:
        
        # Construct a list of thumbnails, in expected size order, largest first
        thumb = R(ICON)
        if group['artwork_url'] != None:
            original_thumb = group['artwork_url']
            ordered_thumbs = [original_thumb.replace('large', 'original'),
                              original_thumb.replace('large', 't500x500'),
                              original_thumb]
            thumb = Resource.ContentsOfURLWithFallback(url = ordered_thumbs, fallback = ICON)

        oc.add(DirectoryObject(key = Callback(ProcessRequest, title = group['name'], params = {}, id = group['id'], type = "group"), title = group['name'], thumb = thumb))

    # Allow the user to move to the next page...
    if len(request) == 30:
        oc.add(NextPageObject(key = Callback(GroupsSearch, query = query, offset = offset + 25), title = 'Next...'))
        
    
    return oc
    
####################################################################################################

def UsersSearch(query = '', offset = 0):
    oc = ObjectContainer(view_group = "InfoList", title2 = query)
    
    # Construct a suitable user URL request...
    request_url = USERS_URL % (CLIENT_ID, query, offset)
    request = JSON.ObjectFromURL(request_url, cacheTime = 0)
    
    if 'errors' in request and len(request['errors'] > 0) and len(request) == 1:
        return MessageContainer("Error", "There are no available items...")
        
    for user in request:
        
        # Construct a list of thumbnails, in expected size order, largest first
        thumb = R(ICON)
        if user['avatar_url'] != None:
            original_thumb = user['avatar_url']
            ordered_thumbs = [original_thumb.replace('large', 'original'),
                              original_thumb.replace('large', 't500x500'),
                              original_thumb]
            thumb = Resource.ContentsOfURLWithFallback(url = ordered_thumbs, fallback = ICON)

        oc.add(DirectoryObject(key = Callback(UserOptions, user = user), title = user['username'], thumb = thumb))
        #oc.add(DirectoryObject(key = Callback(ProcessRequest, title = user['username'], params = {}, id = user['id'], type = "favs"), title = user['username'], thumb = thumb))

    # Allow the user to move to the next page...
    if len(request) == 30:
        oc.add(NextPageObject(key = Callback(UsersSearch, query = query, offset = offset + 25), title = 'Next...'))
        
    
    return oc

####################################################################################################

def UserOptions(user):
    oc = ObjectContainer(view_group = "InfoList", title2 = '')
    
    
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Favorites', params = {}, id = user['id'], type = "favs"), title = 'Favorites'))
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Tracks', params = {}, id = user['id'], type = "user"), title = 'Tracks'))
    
    return oc

####################################################################################################

def Search(query = 'music'):
    return ProcessRequest(title = query, params = {'q': query})

####################################################################################################

@route('/music/soundcloud/{title}', params = dict, offset = int, allow_sync = True)
def ProcessRequest(title, params, offset = 0, id = -1, type = "default"):
    oc = ObjectContainer(view_group = "InfoList", title2 = title)

    if type == 'default':
        # Construct a suitable track URL request...
        request_url = TRACKS_URL % (CLIENT_ID, offset)
        for param, value in params.items():
            request_url = request_url + ('&%s=%s' % (param, value))
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
        return MessageContainer("Error", "There are no available items...")

    for track in request:

        # For some reason, although we've asked for only 'streamable' content, we still sometimes find
        # items which do not have a stream_url. We need to catch these and simply ignore them...
        if track['streamable'] == False:
            continue

        # Construct a list of thumbnails, in expected size order, largest first
        thumb = R(ICON)
        if track['artwork_url'] != None:
            original_thumb = track['artwork_url']
            ordered_thumbs = [original_thumb.replace('large', 'original'),
                              original_thumb.replace('large', 't500x500'),
                              original_thumb]
            thumb = Resource.ContentsOfURLWithFallback(url = ordered_thumbs, fallback = ICON)

        oc.add(TrackObject(
            url = track['stream_url'],
            title = track['title'],
            thumb = thumb,
            duration = int(track['duration'])))

    # Allow the user to move to the next page...
    if len(request) == 30:
        oc.add(NextPageObject(key = Callback(ProcessRequest, title = title, params = params, offset = offset + 25, id = id, type = type), title = 'Next...'))

    return oc
