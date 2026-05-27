import pytest
import pandas as pd
from reconformal.reconformal import RelationshipManager

@pytest.fixture
def rm():
    return RelationshipManager()

def test_remove_duplicate_entities(rm):
    entities_df = pd.DataFrame([
        {'id': 1, 'type': 'Subject', 'details': 'Bob', 'support': 100},
        {'id': 2, 'type': 'Subject', 'details': 'Bob', 'support': 101},
        {'id': 3, 'type': 'Subject', 'details': 'Firefox', 'support': 102}
    ])
    
    cleaned_df = rm.remove_duplicate_entities(entities_df, starting_id=1)
    
    assert len(cleaned_df) == 2
    assert 1 in cleaned_df['id'].values
    assert 2 in cleaned_df['id'].values
    # Bob should have aggregated support [100, 101]
    bob_row = cleaned_df[cleaned_df['details'] == 'Bob'].iloc[0]
    assert bob_row['aggregated_support'] == [100, 101]

def test_update_event_references(rm):
    cleaned_entities_df = pd.DataFrame([
        {'id': 1, 'type': 'Subject', 'details': 'Bob', 'aggregated_support': [100, 101]},
        {'id': 2, 'type': 'Object', 'details': 'https://x.com', 'aggregated_support': [100]}
    ])
    
    events_df = pd.DataFrame([
        {'id': 10, 'support': 100}
    ])
    
    updated_events = rm.update_event_references(events_df, cleaned_entities_df, starting_event_id=1)
    
    assert updated_events.loc[0, 'subjects'] == 1
    assert updated_events.loc[0, 'objects'] == 2
    assert updated_events.loc[0, 'id'] == 1

def test_group_support_relationship(rm):
    footprints_df = pd.DataFrame([
        {'id': 100, 'filename': 'test.csv', 'date_time_min': '2023-01-01', 'type': 'Web Visit'}
    ])
    events_df = pd.DataFrame([
        {'id': 10, 'type': 'Web Visit', 'support': 100}
    ])
    cleaned_entities_df = pd.DataFrame([
        {'id': 1, 'aggregated_support': [100]}
    ])
    
    support = rm.group_support_relationship(footprints_df, cleaned_entities_df, events_df)
    
    assert len(support) == 1
    # Footprint ID, followed by related entity and event IDs -> [100, 1, 10]
    assert set(support[0]) == {100, 1, 10}

def test_list_support_relationship(rm):
    footprints_df = pd.DataFrame([
        {'id': 100, 'filename': 'test.csv', 'date_time_min': '2023-01-01', 'type': 'Web Visit'}
    ])
    events_df = pd.DataFrame([
        {'id': 10, 'type': 'Web Visit', 'support': 100}
    ])
    cleaned_entities_df = pd.DataFrame([
        {'id': 1, 'aggregated_support': [100]}
    ])
    
    support_df = rm.list_support_relationship(footprints_df, cleaned_entities_df, events_df)
    
    assert len(support_df) == 2
    # [100, 1] and [100, 10]
    assert 1 in support_df['entity_id'].values
    assert 10 in support_df['entity_id'].values

def test_list_entity_event_relationship(rm):
    support_df = pd.DataFrame([
        {'footprint_id': 100, 'entity_id': 1},
        {'footprint_id': 100, 'entity_id': 2},
        {'footprint_id': 100, 'entity_id': 10}
    ])
    events_df = pd.DataFrame([
        {'id': 10, 'support': 100}
    ])
    cleaned_entities_df = pd.DataFrame([
        {'id': 1, 'type': 'Subject'},
        {'id': 2, 'type': 'Object'}
    ])
    
    participation = rm.list_entity_event_relationship(
        support_df, cleaned_entities_df, events_df, relation_type='participation'
    )
    
    assert len(participation) == 1
    assert participation['subject_id'].iloc[0] == 1
    assert participation['event_id'].iloc[0] == 10
    
    usage = rm.list_entity_event_relationship(
        support_df, cleaned_entities_df, events_df, relation_type='usage'
    )
    
    assert len(usage) == 1
    assert usage['object_id'].iloc[0] == 2
    assert usage['event_id'].iloc[0] == 10
