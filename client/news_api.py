from client.eds_client import EDSApiClient


class NewsApi:
    """API object for the EDS /News endpoints."""

    def __init__(self, client: EDSApiClient):
        self.client = client

    def url(self, path: str = "") -> str:
        return self.client.news_url(path)

    def get(self, path: str = "", params: dict = None):
        return self.client.get_news(path, params)

    def list(self):
        return self.get()

    def actual(self, category: str = None):
        return self.get("actual", {"category": category} if category is not None else None)

    def calendar(self):
        return self.get("calendar")

    def archived(self, date: str = None):
        return self.get("archived", {"date": date} if date is not None else None)
