import json


def test_create_summary(test_client_with_db):
    response = test_client_with_db.post('api/v1/summaries/', data=json.dumps({'url': 'https://foo.bar'}))

    assert response.status_code == 201
    assert response.json()['url'] == 'https://foo.bar'


def test_create_summaries_invalid_json(test_client):
    response = test_client.post('api/v1/summaries/', data=json.dumps({}))
    assert response.status_code == 422
    assert response.json() == {
        'detail': [{'loc': ['body', 'url'], 'msg': 'field required', 'type': 'value_error.missing'}]
    }
