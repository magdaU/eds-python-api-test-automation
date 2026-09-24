def parse_records(response_json: dict, model):
    return [model(**record) for record in response_json["records"]]
