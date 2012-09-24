
NAME = "SoundCloud"
ART = 'art-default.jpg'
ICON = 'icon-default.png'
ICON_SEARCH = 'icon-search.png'

API_HOST = "api.soundcloud.com"
CLIENT_ID = "4f6c5882fe9cfc80ebf7ff815cd8b383"
CLIENT_SECRET = "b17b970b7a0db3729a1965d2a902efd0"

TRACKS_URL = 'http://api.soundcloud.com/tracks.json?client_id=%s&filter=streamable&offset=%d&limit=30'

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

@handler('/music/soundcloud', NAME, art = ART)
def MainMenu():

    oc = ObjectContainer(title1 = NAME)
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Hot', params = {'order': 'hotness'}), title = 'Hot'))
    oc.add(DirectoryObject(key = Callback(ProcessRequest, title = 'Latest', params = {'order': 'created_at'}), title = 'Latest'))
    oc.add(InputDirectoryObject(key = Callback(Search), title = "Search...", prompt = "Search for Tracks", thumb = R(ICON_SEARCH)))
    return oc

####################################################################################################

def Search(query = 'music'):
    return ProcessRequest(title = query, params = {'q': query})

####################################################################################################

@route('/music/soundcloud/{title}', params = dict, offset = int, allow_sync = True)
def ProcessRequest(title, params, offset = 0):
    oc = ObjectContainer(view_group = "InfoList", title2 = title)

    # Construct a suitable track URL request...
    request_url = TRACKS_URL % (CLIENT_ID, offset)
    for param, value in params.items():
        request_url = request_url + ('&%s=%s' % (param, value))

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
        oc.add(NextPageObject(key = Callback(ProcessRequest, title = title, params = params, offset = offset + 25), title = 'Next...'))

    return oc
