class UriParser:
    uri: str
    website: str
    resource_type: str
    resource_id: str

    def __init__(self, uri):
        self.uri = uri
        self.website, self.resource_type, self.resource_id = uri.split(':')

    @property
    def url(self):
        if self.website == 'youtube' and self.resource_type == 'playlist':
            return f"https://www.youtube.com/playlist?list={self.resource_id}"

        elif self.website == 'youtube' and self.resource_type == 'video':
            return f"https://www.youtube.com/watch?v={self.resource_id}"

        elif self.website == 'spotify':
            return f"https://open.spotify.com/{self.resource_type}/{self.resource_id}"

        else:
            raise Exception(f"Unknown URI '{self.uri}' cannot convert")

    @property
    def thumbnail(self):
        if self.website == 'youtube' and self.resource_type == 'video':
            return f"https://i.ytimg.com/vi/{self.resource_id}/mqdefault.jpg"

        else:
            raise Exception(f"Unknown URI '{self.uri}' cannot convert")
