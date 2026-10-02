from client.eds_client import EDSApiClient


class DatasetApi:
    """API object for one EDS dataset: knows its URL, hides the transport."""

    def __init__(self, client: EDSApiClient, dataset: str):
        self.client = client
        self.dataset = dataset

    @property
    def url(self) -> str:
        return self.client.dataset_url(self.dataset)

    def get(self, limit: int = None, offset: int = None, sort: str = None, filter: dict = None):
        return self.client.get_dataset(self.dataset, limit=limit, offset=offset, sort=sort, filter=filter)
