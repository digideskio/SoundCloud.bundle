import scapi

####################################################################################################

MUSIC_PREFIX = "/music/soundcloud"

NAME = "SoundCloud"

ART = 'art-default.jpg'
ICON = 'icon-default.png'

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
    
    oc = ObjectContainer(view_group="List", title1 = NAME)
    oc.add(DirectoryObject(key = Callback(List, title = 'Hot', order = 'hotness'), title = 'Hot'))
    oc.add(DirectoryObject(key = Callback(List, title = 'Latest', order = 'created_at'), title = 'Latest'))
    return oc

####################################################################################################

def List(title, order):

    oc = ObjectContainer(view_group="InfoList", title1 = title)
    oauth_authenticator = scapi.authentication.OAuthAuthenticator(CLIENT_ID)
    root = scapi.Scope(scapi.ApiConnector(host = API_HOST, authenticator = oauth_authenticator))
    for track in root.tracks(params = {'filter': 'streamable', 'order': order, 'limit': 5}):
        track_url = track.stream_url
        oc.add(TrackObject(
            url = track_url,
            title = track.title,
            thumb = track.artwork_url,
            duration = track.duration,
            genres = [ track.genre ]))

    return oc