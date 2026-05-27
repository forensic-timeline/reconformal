import pytest
import pandas as pd
from reconformal.reconformal import PlasoToFootprint

def test_extract_url():
    # Test chrome_cache
    url = PlasoToFootprint.extract_url("Original URL: https://example.com/test", "chrome_cache")
    assert url == "https://example.com/test"
    
    # Test sqlite/chrome_27_history
    url = PlasoToFootprint.extract_url("https://history.com (Some title)", "sqlite/chrome_27_history")
    assert url == "https://history.com"
    
    # Test sqlite/chrome_66_cookies
    url = PlasoToFootprint.extract_url("https://cookie.com/) Flags: [HTTP only] = False", "sqlite/chrome_66_cookies")
    assert url == "https://cookie.com/"
    
    # Test esedb/msie_webcache
    url = PlasoToFootprint.extract_url("URL: https://msie.com/test", "esedb/msie_webcache")
    assert url == "https://msie.com/test"
    
    # Test sqlite/firefox_history
    url = PlasoToFootprint.extract_url("https://firefox.com/123", "sqlite/firefox_history")
    assert url == "https://firefox.com/123"

def test_detect_browser():
    assert PlasoToFootprint.detect_browser("sqlite/firefox_history", "Some Title") == "Firefox"
    assert PlasoToFootprint.detect_browser("chrome_cache", "Mozilla Firefox") == "Firefox"
    assert PlasoToFootprint.detect_browser("esedb/msie_webcache", "IE Cache") == "Edge"
    assert PlasoToFootprint.detect_browser("other", "Microsoft Edge") == "Edge"
    assert PlasoToFootprint.detect_browser("chrome_cache", "Google") == "Chrome"
    assert PlasoToFootprint.detect_browser("other", "Google Chrome") == "Chrome"
    assert PlasoToFootprint.detect_browser("unknown", "unknown") == "Unknown"

def test_extract_search_term():
    term = PlasoToFootprint.extract_search_term("https://www.bing.com/search?q=mozilla+firefox+download&form=QBLH")
    assert term == "mozilla firefox download"
    
    term = PlasoToFootprint.extract_search_term("https://www.google.com/search?q=test+query")
    assert term == "test query"
    
    term = PlasoToFootprint.extract_search_term("https://example.com/")
    assert term is None

def test_detect_type_and_keys():
    # Web Visit - Bing Search
    row = pd.Series({
        'parser': 'chrome_cache',
        'message': 'Original URL: https://bing.com/search?q=hello+world',
        'display_name': 'Edge'
    })
    res = PlasoToFootprint.detect_type_and_keys(row)
    assert res is not None
    assert res[0] == 'Bing Search'
    assert res[1]['Browser'] == 'Edge'
    assert res[1]['Search_Term'] == 'hello world'

    # Process Creation
    row = pd.Series({
        'parser': 'winevtx',
        'message': '[4688 / 0x1250] New Process Name: C:\\Windows\\System32\\cmd.exe'
    })
    res = PlasoToFootprint.detect_type_and_keys(row)
    assert res is not None
    assert res[0] == 'Process Creation'
    assert res[1]['Executable Name'] == 'cmd.exe'

    # Program Opened
    row = pd.Series({
        'parser': 'prefetch',
        'message': 'Prefetch [CMD.EXE-123456.pf] was executed'
    })
    res = PlasoToFootprint.detect_type_and_keys(row)
    assert res is not None
    assert res[0] == 'Program opened'
    assert res[1]['Program name'] == 'CMD.EXE-123456.pf'

    # Recent File Access
    row = pd.Series({
        'parser': 'winreg/bagmru',
        'message': 'Shell item path: C:\\Users\\Test\\Desktop\\file.txt Index: 1'
    })
    res = PlasoToFootprint.detect_type_and_keys(row)
    assert res is not None
    assert res[0] == 'Recent File Access'
    assert res[1]['file_details_from_entry_shell'] == 'C:\\Users\\Test\\Desktop\\file.txt'

    # File Downloaded
    row = pd.Series({
        'parser': 'sqlite/chrome_27_downloads',
        'message': 'C:\\Users\\Bob\\Downloads\\installer.exe downloaded'
    })
    res = PlasoToFootprint.detect_type_and_keys(row)
    assert res is not None
    assert res[0] == 'File Downloaded'
    assert res[1]['User'] == 'Bob'
    assert res[1]['File Name'] == 'installer.exe'
