import pytest
import pandas as pd
from pathlib import Path
import json
from reconsadfc.reconsadfc import DataProcessor

def test_process_files_single_csv(mocker):
    processor = DataProcessor("dummy.csv")
    
    mocker.patch("pathlib.Path.is_file", return_value=True)
    mocker.patch("pathlib.Path.glob", return_value=[])
    
    mock_df = pd.DataFrame([{'id': 1, 'type': 'Web Visit'}])
    mocker.patch("reconsadfc.reconsadfc.PlasoToFootprint.process_csv", return_value=mock_df)
    
    res = processor.process_files()
    assert len(res) == 1
    assert res.loc[0, 'type'] == 'Web Visit'

def test_process_files_single_json(mocker, tmp_path):
    json_path = tmp_path / "dummy.json"
    data = {
        "1": {"type": "Web Visit", "evidence_source": "WEBHIST"}
    }
    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(data, f)
        
    processor = DataProcessor(str(json_path))
    res = processor.process_files()
    
    assert len(res) == 1
    assert res.loc[0, 'type'] == 'Web Visit'
    assert res.loc[0, 'filename'] == "dummy.json"

def test_process_files_directory(mocker):
    processor = DataProcessor("dummy_dir")
    
    mocker.patch("pathlib.Path.is_file", return_value=False)
    
    mock_csv_1 = Path("file1.csv")
    mock_csv_2 = Path("file2.csv")
    mocker.patch("pathlib.Path.glob", return_value=[mock_csv_1, mock_csv_2])
    
    mock_df_1 = pd.DataFrame([{'type': 'A'}])
    mock_df_2 = pd.DataFrame([{'type': 'B'}])
    
    mocker.patch("reconsadfc.reconsadfc.PlasoToFootprint.process_csv", side_effect=[mock_df_1, mock_df_2])
    
    res = processor.process_files()
    assert len(res) == 2
    assert list(res['type']) == ['A', 'B']
    assert list(res['id']) == [1, 2]
