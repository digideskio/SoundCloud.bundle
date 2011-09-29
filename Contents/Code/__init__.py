import scapi

####################################################################################################

MUSIC_PREFIX = "/music/soundcloud"

NAME = "SoundCloud"

ART = 'art-default.jpg'
ICON = 'icon-default.png'

API_HOST = "api.sandbox-soundcloud.com"
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
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)

####################################################################################################

def MainMenu():
    
    #oauth_authenticator = scapi.authentication.OAuthAuthenticator(CLIENT_ID)
    #root = scapi.Scope(scapi.ApiConnector(host = API_HOST, authenticator = oauth_authenticator))
    #user = root.users(53622)
    #Log("IABI: " + user)
    
    oc = ObjectContainer(view_group="List", title1 = NAME)
    return oc