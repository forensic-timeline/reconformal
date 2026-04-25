import pytest
import pandas as pd
from reconsadfc.reconsadfc import EntityExtractor, KnowledgeRepresentation

@pytest.fixture
def extractor():
    return EntityExtractor()

def test_extract_keys(extractor):
    row_str = pd.Series({'keys': '{"Browser": "Edge"}'})
    res = extractor._extract_keys(row_str)
    assert res == {'Browser': 'Edge'}

    row_dict = pd.Series({'keys': {'Browser': 'Firefox'}})
    res2 = extractor._extract_keys(row_dict)
    assert res2 == {'Browser': 'Firefox'}

    row_invalid = pd.Series({'keys': "invalid"})
    res3 = extractor._extract_keys(row_invalid)
    assert res3 == {}

def test_first_present_value(extractor):
    keys = {'Browser': 'Edge', 'Search_Term': 'test'}
    assert extractor._first_present_value(keys, ['Missing', 'Search_Term']) == 'test'
    assert extractor._first_present_value(keys, ['Missing']) is None

def test_create_entity(extractor):
    entity = extractor._create_entity(1, "Subject", "Bob", 100)
    assert entity['type'] == "Subject"
    assert entity['details'] == "Bob"
    assert entity['id'] == 1
    assert entity['support'] == 100

def test_build_event(extractor):
    row = pd.Series({'type': 'Web Visit', 'filename': 'test.csv', 'date_time_min': '2023-01-01', 'id': 100})
    subjects = [{'id': 1}]
    objects = [{'id': 2}]
    event = extractor._build_event(row, subjects, objects)
    
    assert event['type'] == 'Web Visit'
    assert event['subjects'] == [1]
    assert event['objects'] == [2]
    assert event['support'] == 100

def test_handle_web_visit(extractor):
    row = pd.Series({
        'keys': {'Browser': 'Firefox', 'URL': 'https://example.com'},
        'id': 10
    })
    subjects, objects = extractor._handle_web_visit(row)
    
    assert len(subjects) == 1
    assert subjects[0]['type'] == 'Subject'
    
    assert len(objects) == 1
    assert objects[0]['type'] == 'Object'
