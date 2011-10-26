import scapi

####################################################################################################

MUSIC_PREFIX = "/music/soundcloud"

NAME = "SoundCloud"

ART = 'art-default.jpg'
ICON = 'icon-default.png'
ICON_SEARCH = 'icon-search.png'

API_HOST = "api.soundcloud.com"
CLIENT_ID = "4f6c5882fe9cfc80ebf7ff815cd8b383"
CLIENT_SECRET = "b17b970b7a0db3729a1965d2a902efd0"

####################################################################################################

# This function is initially called by the PMS framework to initialize the plugin. This includes
# setting up the Plugin static instance along with the displayed artwork.
def Start():
    
    # Initialize the plugin
    Plugin.AddPrefixHandler(MUSIC_PREFIX, MainMenu, NAME, ICON, ART)
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

def MainMenu():
    
    oc = ObjectContainer(title1 = NAME)
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Hot', params = {'order': 'hotness'}), title = 'Hot'))
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Latest', params = {'order': 'created_at'}), title = 'Latest'))
    oc.add(InputDirectoryObject(key = Callback(Search), title = "Search...", prompt = "Search for Tracks", thumb = R(ICON_SEARCH)))
    return oc

####################################################################################################

def Search(query):
    return ProcessRequest(title = query, params = {'q': query})

####################################################################################################

def ProcessRequest(title, params, offset = 0):
    oc = ObjectContainer(view_group = "InfoList", title2 = title)

    params['filter'] = 'streamable'
    params['offset'] = str(offset)
    params['limit'] = 25
    
    oauth_authenticator = scapi.authentication.OAuthAuthenticator(CLIENT_ID)
    root = scapi.Scope(scapi.ApiConnector(host = API_HOST, authenticator = oauth_authenticator))
    for track in root.tracks(params = params):
        
        # For some reason, although we've asked for only 'streamable' content, we still sometimes find
        # items which do not have a stream_url. We need to catch these and simply ignore them...
        if track.streamable == False:
            continue
        
        # Request larger thumbnails. As documented by the API, we simply replace the default 'large'
        # with the one that we actually want.
        thumb = track.artwork_url
        if thumb != None:
           thumb = thumb.replace('large','original')
        
        oc.add(TrackObject(
            url = track.stream_url,
            title = track.title,
            thumb = thumb,
            duration = int(track.duration)))

    # Allow the user to move to the next page...
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = title, params = params, offset = offset + 25), title = 'Next...'))
    
    return oc
