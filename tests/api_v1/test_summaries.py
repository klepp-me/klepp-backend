import json


def test_create_summary(test_app_with_db):
    response = test_app_with_db.post('api/v1/summaries/', data=json.dumps({'url': 'https://foo.bar'}))

    assert response.status_code == 201
    assert response.json()['url'] == 'https://foo.bar'
