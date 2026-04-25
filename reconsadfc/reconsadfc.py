import json
import argparse
import sys
import re
import os
import pandas as pd
from typing import List
from collections import Counter
import matplotlib.pyplot as plt
from pathlib import Path

class PlasoToFootprint:
    RELEVANT_PARSERS = {
        'chrome_cache', 'sqlite/chrome_27_history', 'sqlite/chrome_66_cookies',
        'esedb/msie_webcache', 'sqlite/firefox_history', 'sqlite/firefox_cookies',
        'winevtx', 'prefetch', 'winreg/userassist', 'winreg/bam', 'winpca_dic',
        'winreg/bagmru', 'winlnk', 'sqlite/chrome_27_downloads', 'sqlite/firefox_downloads',
    }

    def __init__(self):
        pass

    @staticmethod
    def extract_url(message: str, parser: str) -> str:
        if parser == 'chrome_cache':
            match = re.search(r'Original URL:\s*(https?://\S+)', message)
            return match.group(1) if match else None
        elif parser == 'sqlite/chrome_27_history':
            match = re.match(r'(https?://\S+)', message)
            return match.group(1) if match else None
        elif parser == 'sqlite/chrome_66_cookies':
            match = re.match(r'(https?://\S+)', message)
            return match.group(1).rstrip(')') if match else None
        elif parser == 'esedb/msie_webcache':
            match = re.search(r'URL:\s*(https?://\S+)', message)
            return match.group(1) if match else None
        elif parser == 'sqlite/firefox_history':
            match = re.match(r'(https?://\S+)', message)
            return match.group(1) if match else None
        return None

    @staticmethod
    def detect_browser(parser: str, display_name: str) -> str:
        display_lower = str(display_name).lower()
        if 'firefox' in display_lower or 'firefox' in parser:
            return 'Firefox'
        if 'edge' in display_lower or 'msie' in parser or 'msie_webcache' in parser:
            return 'Edge'
        if 'chrome' in parser or 'chrome' in display_lower:
            return 'Chrome'
        return 'Unknown'

    @staticmethod
    def extract_search_term(url: str) -> str:
        if not url:
            return None
        match = re.search(r'[?&]q=([^&]+)', url)
        if match:
            return match.group(1).replace('+', ' ')
        return None

    @classmethod
    def detect_type_and_keys(cls, row: pd.Series):
        parser = str(row.get('parser', ''))
        message = str(row.get('message', ''))
        display_name = str(row.get('display_name', ''))

        # Web Visit / Bing Search / Google Search
        if parser in ('chrome_cache', 'sqlite/chrome_27_history',
                      'sqlite/chrome_66_cookies', 'esedb/msie_webcache',
                      'sqlite/firefox_history', 'sqlite/firefox_cookies'):
            url = cls.extract_url(message, parser)
            if not url:
                return None
            browser = cls.detect_browser(parser, display_name)

            if re.search(r'bing\.com/search', url):
                term = cls.extract_search_term(url)
                return ('Bing Search', {'Browser': browser, 'Search_Term': term or url}, None, None)
            if re.search(r'google\.com/search', url):
                term = cls.extract_search_term(url)
                return ('Google Search', {'Browser': browser, 'Search_Term': term or url}, None, None)
            return ('Web Visit', {'Browser': browser, 'URL': url}, None, None)

        # Process Creation
        elif parser == 'winevtx':
            eid_match = re.search(r'\[(\d+)\s*/', message)
            eid = int(eid_match.group(1)) if eid_match else 0

            if eid == 4688:
                proc_match = re.search(r'New Process Name:\s*(\S+)', message)
                if not proc_match:
                    proc_match = re.search(r"'([^']+\.exe)'", message, re.IGNORECASE)
                exe = proc_match.group(1) if proc_match else 'unknown.exe'
                return ('Process Creation', {'Executable Name': os.path.basename(exe)}, parser, None)

            if eid in (1074, 1076, 6006, 6008, 13, 41):
                return ('Shutdown time', {'Windows Event ID': str(eid)}, parser, None)

            return None

        # Program opened
        elif parser == 'prefetch':
            match = re.search(r'Prefetch \[(.+?)\] was executed', message)
            prog = match.group(1) if match else 'unknown.exe'
            return ('Program opened', {'Program name': prog}, parser, None)

        elif parser == 'winreg/userassist':
            match = re.search(r'Value name:\s*(.+\.exe)', message, re.IGNORECASE)
            if match:
                prog = os.path.basename(match.group(1).strip())
                return ('Program opened', {'Program name': prog}, parser, None)
            return None

        elif parser == 'winreg/bam':
            match = re.search(r'\\([^\\]+\.exe)', message, re.IGNORECASE)
            if match:
                return ('Program opened', {'Program name': match.group(1)}, parser, None)
            return None

        elif parser == 'winpca_dic':
            match = re.search(r'\[(.+?\.exe)\]', message, re.IGNORECASE)
            if match:
                prog = os.path.basename(match.group(1).strip())
                return ('Program opened', {'Program name': prog}, parser, None)
            return None

        # Recent File Access
        elif parser == 'winreg/bagmru':
            path_match = re.search(r'Shell item path:\s*(.+?)(?:\s+Index:|$)', message)
            if path_match:
                file_path = path_match.group(1).strip()
                return ('Recent File Access', {'file_details_from_entry_shell': file_path}, parser, file_path)
            return None

        elif parser == 'winlnk':
            return ('Recent File Access', {'file_details_from_lnk': message[:200]}, parser, display_name)

        # File Download
        elif parser in ('sqlite/chrome_27_downloads', 'sqlite/firefox_downloads'):
            match = re.search(r'(\S+\.(?:exe|zip|msi|dmg|pkg|pdf|docx?))', message, re.IGNORECASE)
            fname = match.group(1) if match else message[:100]
            user_match = re.search(r'Users\\([^\\]+)\\', message)
            user = user_match.group(1) if user_match else 'User'
            return ('File Downloaded', {'User': user, 'File Name': os.path.basename(fname)}, parser, None)

        return None

    @classmethod
    def process_csv(cls, csv_path: str, output_path: str = None) -> pd.DataFrame:
        df = pd.read_csv(csv_path)

        df = df[df['parser'].isin(cls.RELEVANT_PARSERS)].copy()
        df = df.reset_index(drop=True)

        result_list = []
        for idx, row in df.iterrows():
            parsed = cls.detect_type_and_keys(row)
            if parsed is None:
                continue

            f_type, keys, plugin, files = parsed
            
            # The EntityExtractor also wants 'filename' and 'id' dynamically populated 
            # where appropriate. Plaso CSVs usually have a filename column, so we keep that if it exists.
            # `id` typically comes from index or dataframe index.
            entry = {
                'id': idx,
                'filename': str(row.get('filename', os.path.basename(csv_path))),
                'date_time_min': str(row.get('datetime', '')),
                'date_time_max': str(row.get('datetime', '')),
                'evidence_source': str(row.get('source', '')),
                'type': f_type,
                'description': str(row.get('message', ''))[:300],
                'category': str(row.get('source_long', '')),
                'plugin': plugin,
                'files': files,
                'keys': keys,
                'supporting': None,
                'trigger': None,
            }
            result_list.append(entry)

        res_df = pd.DataFrame(result_list)

        if output_path is not None:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            res_dict = {str(i): row.to_dict() for i, row in res_df.iterrows()}
            with open(output_path, 'w') as f:
                json.dump(res_dict, f, indent=2, default=str)
                
        return res_df

class DataProcessor:
    def __init__(self, file_dir: str):
        """
        Initialize file-processing configuration.

        :param file_dir: Directory path containing input CSV files.
        :type file_dir: str
        """
        self.file_dir = file_dir
        self.directory = Path(file_dir)
        self.combined_data = pd.DataFrame() 
    
    def process_files(self) -> pd.DataFrame:
        """
        Read CSV files from the configured directory and keep only WEBHIST rows.

        The filtered rows from all files are concatenated into a single DataFrame.

        :returns: Combined filtered data from all matching CSV files.
        :rtype: pandas.DataFrame
        """
        filtered_dfs = []

        if self.directory.is_file():
            files_to_process = [self.directory]
        else:
            files_to_process = list(self.directory.glob("*.csv"))
        
        for filepath in files_to_process:
            if filepath.suffix.lower() == '.csv':
                filtered_df = PlasoToFootprint.process_csv(str(filepath), None)
            elif filepath.suffix.lower() == '.json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                filtered_df = pd.DataFrame.from_dict(data, orient='index')
                if 'filename' not in filtered_df.columns:
                    filtered_df['filename'] = filepath.name
            else:
                continue
            
            if not filtered_df.empty:
                filtered_dfs.append(filtered_df)
            
        if filtered_dfs:
            self.combined_data = pd.concat(filtered_dfs, ignore_index=True)
            self.combined_data['id'] = range(1, len(self.combined_data) + 1)
            
        print("Filtered data has been processed")
        return self.combined_data

class EntityExtractor:
    def __init__(self):
        """
        Initialize internal buffers and ID counters used during extraction.

        :returns: None
        :rtype: None
        """
        self.objects = []
        self.subjects = []
        self.events = []
        self.current_object_id = 0
        self.current_subject_id = 0
        self.current_event_id = 0

    def extract_entities(self, df: pd.DataFrame) -> tuple:
        """
        Extract subjects, objects, and events from footprint rows.

        Event-type handlers are selected dynamically from each row's ``type`` value.
        Extracted entities are accumulated and then returned as three DataFrames.

        :param df: Input footprint DataFrame.
        :type df: pandas.DataFrame
        :returns: Tuple of ``(objects_df, subjects_df, events_df)``.
        :rtype: tuple
        """
        df_len = len(df)
        self.current_object_id = df_len + 1
        self.current_subject_id = self.current_object_id + df_len
        self.current_event_id = self.current_subject_id + df_len
        
        event_types = {
            "Web Visit": self._handle_web_visit,
            "Process Creation": self._handle_process_creation,
            "Program opened": self._handle_program_opened,
            "Recent File Access": self._handle_recent_file_access,
            "Google Search": self._handle_google_search,
            "Bing Search": self._handle_bing_search,
            "Shutdown time": self._handle_shutdown_time,
            "File Downloaded": self._handle_file_downloaded
        }

        for idx, row in df.iterrows():
            event_type = row['type']
            subjects = []
            objects = []

            if event_type in event_types:
                subjects, objects = event_types[event_type](row)

            self.subjects.extend(subjects)
            self.objects.extend(objects)

            event = self._build_event(row, subjects, objects)
            self.events.append(event)

            self.current_object_id += len(objects)
            self.current_subject_id += len(subjects)
            self.current_event_id += 1

        return pd.DataFrame(self.objects), pd.DataFrame(self.subjects), pd.DataFrame(self.events)

    @staticmethod
    def _extract_keys(row: pd.Series) -> dict:
        """
        Normalize the ``keys`` field from a footprint row into a dictionary.

        Supports raw dictionaries and JSON-encoded strings. If parsing fails,
        an empty dictionary is returned.

        :param row: Source row containing a potential ``keys`` column.
        :type row: pandas.Series
        :returns: Parsed keys dictionary.
        :rtype: dict
        """
        keys = row.get("keys", {})
        if isinstance(keys, dict):
            return keys
        if isinstance(keys, str):
            try:
                parsed = json.loads(keys)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    @staticmethod
    def _first_present_value(data: dict, candidates: List[str]):
        """
        Return the first non-null value among candidate keys.

        :param data: Dictionary to inspect.
        :type data: dict
        :param candidates: Ordered key names to check.
        :type candidates: List[str]
        :returns: First available non-null value, or None.
        :rtype: Any
        """
        for key in candidates:
            if key in data and pd.notna(data[key]):
                return data[key]
        return None
    
    def _create_entity(self, entity_id: int, entity_type: str, details: dict, support_id: int) -> dict:
        """
        Build a standardized entity dictionary.

        :param entity_id: Unique entity identifier.
        :type entity_id: int
        :param entity_type: Entity category (for example, Subject or Object).
        :type entity_type: str
        :param details: Entity attributes.
        :type details: dict
        :param support_id: Source footprint identifier supporting this entity.
        :type support_id: int
        :returns: Normalized entity record.
        :rtype: dict
        """
        return {'id': entity_id, 'type': entity_type, 'details': details, 'support': support_id}
    
    def _build_event(self, row: pd.Series, subjects: list, objects: list) -> dict:
        """
        Build a normalized event dictionary from a footprint row.

        :param row: Footprint row.
        :type row: pandas.Series
        :param subjects: Extracted subject entities for the row.
        :type subjects: list
        :param objects: Extracted object entities for the row.
        :type objects: list
        :returns: Event record referencing extracted subject/object IDs.
        :rtype: dict
        """
        return {
            'id': self.current_event_id,
            'type': row['type'],
            'filename': row['filename'],
            'time': row.get("date_time_min"),
            'subjects': [s['id'] for s in subjects],
            'objects': [o['id'] for o in objects],
            'related_events': [],
            'support': row['id']
        }

    def _handle_web_visit(self, row: pd.Series) -> tuple:
        """
        Extract subject and object entities for ``Web Visit`` events.

        :param row: Footprint row.
        :type row: pandas.Series
        :returns: Tuple of ``(subjects, objects)`` extracted from the row.
        :rtype: tuple
        """
        subjects = []
        objects = []

        keys = self._extract_keys(row)
        if "Browser" in keys:
            subjects.append(self._create_entity(self.current_subject_id, 'Subject', {'browser': keys["Browser"]}, row['id']))
        if "URL" in keys:
            objects.append(self._create_entity(self.current_object_id, 'Object', {'url': keys["URL"]}, row['id']))
        
        return subjects, objects

    def _handle_process_creation(self, row: pd.Series) -> tuple:
        """
        Extract subject and object entities for ``Process Creation`` events.

        :param row: Footprint row.
        :type row: pandas.Series
        :returns: Tuple of ``(subjects, objects)`` extracted from the row.
        :rtype: tuple
        """
        subjects = []
        objects = []

        keys = self._extract_keys(row)
        executable_name = self._first_present_value(keys, ["Executable Name", "Executable name"])
        if executable_name is not None:
            subjects.append(self._create_entity(self.current_subject_id, 'Subject', {'executable_name': executable_name}, row['id']))
        if row.get("plugin"):
            objects.append(self._create_entity(self.current_object_id, 'Object', {'plugin': row["plugin"]}, row['id']))

        return subjects, objects
    
    def _handle_program_opened(self, row: pd.Series) -> tuple:
        """
        Extract subject and object entities for ``Program opened`` events.

        :param row: Footprint row.
        :type row: pandas.Series
        :returns: Tuple of ``(subjects, objects)`` extracted from the row.
        :rtype: tuple
        """
        subjects = []
        objects = []

        keys = self._extract_keys(row)
        if "Program name" in keys:
            subjects.append(self._create_entity(self.current_subject_id, 'Subject', {'program_name': keys["Program name"]}, row['id']))
        if row.get("plugin"):
            objects.append(self._create_entity(self.current_object_id, 'Object', {'plugin': row["plugin"]}, row['id']))
        
        return subjects, objects

    def _handle_recent_file_access(self, row: pd.Series) -> tuple:
        """
        Extract subject and object entities for ``Recent File Access`` events.

        :param row: Footprint row.
        :type row: pandas.Series
        :returns: Tuple of ``(subjects, objects)`` extracted from the row.
        :rtype: tuple
        """
        subjects = []
        objects = []

        keys = self._extract_keys(row)
        if row.get("files"):
            subjects.append(self._create_entity(self.current_subject_id, 'Subject', {'file_path': row["files"]}, row['id']))
        if "file_details_from_lnk" in keys:
            objects.append(self._create_entity(self.current_object_id, 'Object', {'file_details_from_lnk': keys.get("file_details_from_lnk")}, row['id']))
        elif  "file_details_from_entry_shell" in keys:
            objects.append(self._create_entity(self.current_object_id, 'Object', {'file_details_from_entry_shell': keys.get("file_details_from_entry_shell")}, row['id']))
        
        return subjects, objects

    def _handle_google_search(self, row: pd.Series) -> tuple:
        """
        Extract subject and object entities for ``Google Search`` events.

        :param row: Footprint row.
        :type row: pandas.Series
        :returns: Tuple of ``(subjects, objects)`` extracted from the row.
        :rtype: tuple
        """
        subjects = []
        objects = []

        keys = self._extract_keys(row)
        if "Browser" in keys:
            subjects.append(self._create_entity(self.current_subject_id, 'Subject', {'browser': keys["Browser"]}, row['id']))
        if "Search_Term" in keys:
            objects.append(self._create_entity(self.current_object_id, 'Object', {'search_term': keys["Search_Term"]}, row['id']))
        
        return subjects, objects

    def _handle_shutdown_time(self, row: pd.Series) -> tuple:
        """
        Extract subject and object entities for ``Shutdown time`` events.

        :param row: Footprint row.
        :type row: pandas.Series
        :returns: Tuple of ``(subjects, objects)`` extracted from the row.
        :rtype: tuple
        """
        subjects = []
        objects = []

        keys = self._extract_keys(row)
        subjects.append(self._create_entity(self.current_subject_id, 'Subject', {'name': 'Windows'}, row['id']))
        if "Windows Event ID" in keys:
            objects.append(self._create_entity(self.current_object_id, 'Object', {'windows_event_id': keys["Windows Event ID"]}, row['id']))
        
        return subjects, objects
    
    def _handle_bing_search(self, row: pd.Series) -> tuple:
        """
        Extract subject and object entities for ``Bing Search`` events.

        :param row: Footprint row.
        :type row: pandas.Series
        :returns: Tuple of ``(subjects, objects)`` extracted from the row.
        :rtype: tuple
        """
        subjects = []
        objects = []

        keys = self._extract_keys(row)
        if "User" in keys:
            subjects.append(self._create_entity(self.current_subject_id, 'Subject',{'user': keys["User"]}, row['id']))
        if "Search_Term" in keys:
            objects.append(self._create_entity(self.current_object_id, 'Object', {'search_term': keys["Search_Term"]}, row['id']))
        
        return subjects, objects
    
    def _handle_file_downloaded(self, row: pd.Series) -> tuple:
        """
        Extract subject and object entities for ``File Downloaded`` events.

        :param row: Footprint row.
        :type row: pandas.Series
        :returns: Tuple of ``(subjects, objects)`` extracted from the row.
        :rtype: tuple
        """
        subjects = []
        objects = []

        keys = self._extract_keys(row)
        if "Browser" in keys:
            subjects.append(self._create_entity(self.current_subject_id, 'Subject', {'browser': keys["Browser"]}, row['id']))

        file_name = self._first_present_value(keys, ["File Name", "File name"])
        if file_name is not None:
            objects.append(self._create_entity(self.current_object_id, 'Object', {'file_name': file_name}, row['id']))
        
        return subjects, objects

class RelationshipManager:
    def remove_duplicate_entities(self, df: pd.DataFrame, starting_id: int) -> pd.DataFrame:
        """
        Deduplicate entity rows and aggregate their support references.

        Entities are considered duplicates when both their type and serialized
        details are equal.

        :param df: DataFrame containing entity rows.
        :type df: pandas.DataFrame
        :param starting_id: Starting ID for rebuilt unique entities.
        :type starting_id: int
        :returns: Deduplicated entity DataFrame with ``aggregated_support`` lists.
        :rtype: pandas.DataFrame
        """
        unique_entities: dict = {}

        for _, row in df.iterrows():
            details_str = json.dumps(row['details'], sort_keys=True)
            key = (row['type'], details_str)

            if key in unique_entities:
                unique_entities[key]['support'].append(row['support'])
            else:
                unique_entities[key] = {
                    'type': row['type'],
                    'support': [row['support']]
                }

        cleaned_list = []
        current_id = starting_id
        for (entity_type, details_str), values in unique_entities.items():
            cleaned_list.append({
                'id': current_id,
                'type': entity_type,
                'details': json.loads(details_str),
                'aggregated_support': values['support']
            })
            current_id += 1

        self.next_available_id = current_id
        return pd.DataFrame(cleaned_list)

    def update_event_references(self, events_df: pd.DataFrame, cleaned_entities_df: pd.DataFrame, starting_event_id: int) -> pd.DataFrame:
        """
        Reassign event IDs and map subject/object references to deduplicated entities.

        :param events_df: Raw events DataFrame.
        :type events_df: pandas.DataFrame
        :param cleaned_entities_df: Deduplicated entities DataFrame.
        :type cleaned_entities_df: pandas.DataFrame
        :param starting_event_id: First event ID to assign.
        :type starting_event_id: int
        :returns: Updated events DataFrame with remapped IDs and entity references.
        :rtype: pandas.DataFrame
        """
        events_df = events_df.copy()

        events_df['id'] = range(starting_event_id, starting_event_id + len(events_df))

        def find_entity_id(support_value: int, entity_type: str):
            """
            Find an entity ID matching a support reference and entity type.

            :param support_value: Footprint support ID to match.
            :type support_value: int
            :param entity_type: Target entity type (Subject or Object).
            :type entity_type: str
            :returns: Matching entity ID, or None when no match exists.
            :rtype: int or None
            """
            mask = (cleaned_entities_df['type'] == entity_type) & (cleaned_entities_df['aggregated_support'].apply(lambda s: support_value in s))
            match = cleaned_entities_df.loc[mask]
            return match.iloc[0]['id'] if not match.empty else None

        events_df['subjects'] = events_df['support'].apply(lambda s: find_entity_id(s, 'Subject'))
        events_df['objects'] = events_df['support'].apply(lambda s: find_entity_id(s, 'Object'))

        return events_df

    def group_support_relationship(
        self,
        footprints_df: pd.DataFrame,
        cleaned_entities_df: pd.DataFrame,
        events_df: pd.DataFrame
    ) -> list:
        """
        Group each footprint with all related entity and event IDs.

        :param footprints_df: Footprint DataFrame.
        :type footprints_df: pandas.DataFrame
        :param cleaned_entities_df: Deduplicated entities DataFrame.
        :type cleaned_entities_df: pandas.DataFrame
        :param events_df: Events DataFrame.
        :type events_df: pandas.DataFrame
        :returns: List where each element starts with footprint ID followed by related IDs.
        :rtype: list
        """
        support = []

        for _, row in footprints_df.iterrows():
            footprint_id = row['id']
            related_ids = [footprint_id]

            entity_ids = cleaned_entities_df.loc[
                cleaned_entities_df['aggregated_support'].apply(
                    lambda x: footprint_id in x
                ), 'id'
            ].tolist()

            event_ids = events_df.loc[
                events_df['support'] == footprint_id, 'id'
            ].tolist()

            related_ids.extend(entity_ids)
            related_ids.extend(event_ids)
            support.append(related_ids)

        return support

    def list_support_relationship(self, footprints_df: pd.DataFrame, cleaned_entities_df: pd.DataFrame, events_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create pairwise support relationships between footprints and linked IDs.

        :param footprints_df: Footprint DataFrame.
        :type footprints_df: pandas.DataFrame
        :param cleaned_entities_df: Deduplicated entities DataFrame.
        :type cleaned_entities_df: pandas.DataFrame
        :param events_df: Events DataFrame.
        :type events_df: pandas.DataFrame
        :returns: DataFrame with ``footprint_id`` and ``entity_id`` columns.
        :rtype: pandas.DataFrame
        """
        support_ = []

        for footprint_id in footprints_df['id']:
            entity_ids = cleaned_entities_df.loc[cleaned_entities_df['aggregated_support'].apply(lambda x: footprint_id in x), 'id'].tolist()
            for entity_id in entity_ids:
                support_.append([footprint_id, entity_id])

            event_ids = events_df.loc[events_df['support'] == footprint_id, 'id'].tolist()
            for event_id in event_ids:
                support_.append([footprint_id, event_id])

        return pd.DataFrame(support_, columns=['footprint_id', 'entity_id'])

    def list_entity_event_relationship(self, support_df: pd.DataFrame, cleaned_entities_df: pd.DataFrame, events_df: pd.DataFrame, relation_type: str = 'participation') -> pd.DataFrame:
        """
        Build entity-event relationships for participation or usage views.

        :param support_df: Pairwise support relationship DataFrame.
        :type support_df: pandas.DataFrame
        :param cleaned_entities_df: Deduplicated entities DataFrame.
        :type cleaned_entities_df: pandas.DataFrame
        :param events_df: Events DataFrame.
        :type events_df: pandas.DataFrame
        :param relation_type: Relationship mode, either ``participation`` or ``usage``.
        :type relation_type: str
        :returns: Relationship DataFrame for the selected mode.
        :rtype: pandas.DataFrame
        :raises ValueError: If relation_type is not supported.
        """
        if relation_type == 'participation':
            entity_type = 'Subject'
            pair_builder = lambda eid, evid, fpid: {
                'subject_id': eid, 'event_id': evid, 'footprint_id': fpid
            }
        elif relation_type == 'usage':
            entity_type = 'Object'
            pair_builder = lambda eid, evid, fpid: {
                'event_id': evid, 'object_id': eid, 'footprint_id': fpid
            }
        else:
            raise ValueError(f"relation_type must be 'participation' or 'usage', got '{relation_type}'")

        entity_id_set = set(cleaned_entities_df.loc[cleaned_entities_df['type'] == entity_type, 'id'])

        relationships = []
        for _, pair in support_df.iterrows():
            footprint_id = pair['footprint_id']
            entity_id = pair['entity_id']

            if entity_id in entity_id_set:
                event_ids = events_df.loc[events_df['support'] == footprint_id, 'id'].tolist()
                for event_id in event_ids:
                    relationships.append(pair_builder(entity_id, event_id, footprint_id))

        return pd.DataFrame(relationships)


class KnowledgeRepresentation:
    def __init__(self, combined_data: pd.DataFrame):
        """
        Initialize knowledge representation containers.

        :param combined_data: Preprocessed footprint DataFrame.
        :type combined_data: pandas.DataFrame
        """
        self.combined_data = combined_data

        # These are populated by extract_entities()
        self.cleaned_entities_df: pd.DataFrame = pd.DataFrame()
        self.events_df:           pd.DataFrame = pd.DataFrame()
        self.support:             list         = []
        self.support_df:          pd.DataFrame = pd.DataFrame()
        self.participation_df:    pd.DataFrame = pd.DataFrame()
        self.usage_df:            pd.DataFrame = pd.DataFrame()

    def sort_data(self) -> pd.DataFrame:
        """
        Normalize and sort footprint data by timestamp.

        Converts ``date_time_min`` to datetime, removes timezone information,
        sorts ascending, and assigns a sequential ``id`` column.

        :returns: Sorted and normalized footprint DataFrame.
        :rtype: pandas.DataFrame
        """
        self.combined_data['date_time_min'] = pd.to_datetime(
            self.combined_data['date_time_min'], errors='coerce'
        )
        self.combined_data['date_time_min'] = (
            self.combined_data['date_time_min'].dt.tz_localize(None)
        )
        self.combined_data = (
            self.combined_data
            .sort_values(by='date_time_min')
            .reset_index(drop=True)
        )
        self.combined_data['id'] = self.combined_data.index + 1
        return self.combined_data

    def extract_entities(self) -> None:
        """
        Execute entity extraction and build all derived relationship datasets.

        Populates ``cleaned_entities_df``, ``events_df``, support structures,
        participation, and usage tables on the current instance.

        :returns: None
        :rtype: None
        """
        footprints_df = self.combined_data

        extractor = EntityExtractor()
        objects_df, subjects_df, raw_events_df = extractor.extract_entities(footprints_df)
        all_entities_df = pd.concat([objects_df, subjects_df], ignore_index=True)

        rm = RelationshipManager()
        self.cleaned_entities_df = rm.remove_duplicate_entities(
            all_entities_df,
            starting_id=len(footprints_df) + 1
        )

        self.events_df = rm.update_event_references(
            raw_events_df,
            self.cleaned_entities_df,
            starting_event_id=rm.next_available_id
        )

        self.support = rm.group_support_relationship(
            footprints_df, self.cleaned_entities_df, self.events_df
        )
        self.support_df = rm.list_support_relationship(
            footprints_df, self.cleaned_entities_df, self.events_df
        )
        self.participation_df = rm.list_entity_event_relationship(
            self.support_df, self.cleaned_entities_df, self.events_df,
            relation_type='participation'
        )
        self.usage_df = rm.list_entity_event_relationship(
            self.support_df, self.cleaned_entities_df, self.events_df,
            relation_type='usage'
        )

class Correlation_Calculator:
    def __init__(self):
        """
        Initialize a calculator for temporal and contextual event correlation.

        :returns: None
        :rtype: None
        """
        pass

    def starts(self, e_start, x_start):
        """
        Check the Allen ``starts`` relation for point-like events.

        :param e_start: Start time of the first event.
        :param x_start: Start time of the second event.
        :returns: 1 when start times are equal, otherwise 0.
        :rtype: int
        """
        return int(e_start == x_start)
    
    def equals(self, e_start, e_end, x_start, x_end):
        """
        Check whether two event intervals are equal.

        :param e_start: Start time of the first event.
        :param e_end: End time of the first event.
        :param x_start: Start time of the second event.
        :param x_end: End time of the second event.
        :returns: 1 when both intervals are identical, otherwise 0.
        :rtype: int
        """
        return int(e_start == x_start and e_end == x_end)
    
    def meets(self, e_end, x_start):
        """
        Check the Allen ``meets`` relation.

        :param e_end: End time of the first event.
        :param x_start: Start time of the second event.
        :returns: 1 when first end equals second start, otherwise 0.
        :rtype: int
        """
        return int(e_end == x_start)

    def overlaps(self, e_start, e_end, x_start, x_end):
        """
        Check whether the first interval overlaps the second at its start.

        :param e_start: Start time of the first event.
        :param e_end: End time of the first event.
        :param x_start: Start time of the second event.
        :param x_end: End time of the second event.
        :returns: 1 when overlap condition is satisfied, otherwise 0.
        :rtype: int
        """
        return int(e_start < x_start and e_end > x_start)

    def during(self, e_start, e_end, x_start, x_end):
        """
        Check whether the first interval is strictly during the second.

        :param e_start: Start time of the first event.
        :param e_end: End time of the first event.
        :param x_start: Start time of the second event.
        :param x_end: End time of the second event.
        :returns: 1 when first interval is contained by second, otherwise 0.
        :rtype: int
        """
        return int(e_start > x_start and e_end < x_end)

    def finishes(self, e_end, x_end):
        """
        Check the Allen ``finishes`` relation endpoint equality.

        :param e_end: End time of the first event.
        :param x_end: End time of the second event.
        :returns: 1 when end times are equal, otherwise 0.
        :rtype: int
        """
        return int(e_end == x_end)

    def before(self, e_end, x_start):
        """
        Score how strongly the first event occurs before the second.

        Uses inverse distance in seconds when ``x_start`` is after ``e_end``;
        returns 0 otherwise.

        :param e_end: End time of the first event.
        :param x_start: Start time of the second event.
        :returns: Inverse temporal distance score or 0.
        :rtype: float
        """
        if x_start > e_end:
            return 1 / (x_start - e_end).total_seconds()
        else:
            return 0
        
    @staticmethod
    def subject_correlation(subject_e, subject_x):
        """
        Compute overlap ratio between subject sets.

        Inputs can be a single subject identifier or a list of identifiers.

        :param subject_e: Subject identifier(s) for the first event.
        :param subject_x: Subject identifier(s) for the second event.
        :returns: Intersection size divided by max input size.
        :rtype: float
        """
        subject_e = subject_e if isinstance(subject_e, list) else [subject_e]
        subject_x = subject_x if isinstance(subject_x, list) else [subject_x]

        intersection = len(set(subject_e).intersection(set(subject_x)))
        max_size = max(len(subject_e), len(subject_x))
        return intersection / max_size if max_size > 0 else 0

    @staticmethod
    def object_correlation(object_e, object_x):
        """
        Compute overlap ratio between object sets.

        Inputs can be a single object identifier or a list of identifiers.

        :param object_e: Object identifier(s) for the first event.
        :param object_x: Object identifier(s) for the second event.
        :returns: Intersection size divided by max input size.
        :rtype: float
        """
        object_e = object_e if isinstance(object_e, list) else [object_e]
        object_x = object_x if isinstance(object_x, list) else [object_x]

        intersection = len(set(object_e).intersection(set(object_x)))
        max_size = max(len(object_e), len(object_x))
        return intersection / max_size if max_size > 0 else 0
    

class TimelineReconstruction:
    def __init__(self, knowledge_representation: KnowledgeRepresentation):
        """
        Initialize timeline reconstruction utilities.

        :param knowledge_representation: Prepared knowledge representation instance.
        :type knowledge_representation: KnowledgeRepresentation
        """
        self.kr = knowledge_representation
        self.alpha = 1
        self.correlation_calculator = Correlation_Calculator()

    def reconstruct_timeline(self) -> pd.DataFrame:
        """
        Build a deduplicated timeline view from event data.

        :returns: Timeline DataFrame containing ID, time, type, subjects, and objects.
        :rtype: pandas.DataFrame
        """
        timeline_df = self.kr.events_df[["id", "time", "type", "subjects", "objects"]].copy()
        timeline_df = timeline_df.drop_duplicates(subset=["time", "type", "subjects", "objects"]).reset_index(drop=True)

        return timeline_df

    def calculate_correlation(self, timeline_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Compute pairwise correlations between events in a timeline.

        For each ordered event pair ``(event_1, event_2)`` where IDs differ, this
        method computes temporal, subject, object, and total correlation values.

        :param timeline_df: Optional timeline DataFrame. When omitted, it is
                            reconstructed from the knowledge representation.
        :type timeline_df: pandas.DataFrame or None
        :returns: Pairwise correlation DataFrame.
        :rtype: pandas.DataFrame
        """
        if timeline_df is None:
            timeline_df = self.reconstruct_timeline()

        correlations = []
        for i, event_1 in timeline_df.iterrows():
            for j, event_2 in timeline_df.iterrows():
                if i != j:
                    e_start, e_end = event_1['time'], event_1['time']  
                    x_start, x_end = event_2['time'], event_2['time']

                    temporal_corr = (
                        self.alpha * self.correlation_calculator.starts(e_start, x_start) +
                        self.alpha * self.correlation_calculator.equals(e_start, e_end, x_start, x_end) +
                        self.correlation_calculator.meets(e_end, x_start) +
                        self.correlation_calculator.overlaps(e_start, e_end, x_start, x_end) +
                        self.correlation_calculator.during(e_start, e_end, x_start, x_end) +
                        self.correlation_calculator.finishes(e_end, x_end) +
                        self.correlation_calculator.before(e_end, x_start)
                    )

                    subject_corr = self.correlation_calculator.subject_correlation(event_1['subjects'], event_2['subjects'])
                    object_corr = self.correlation_calculator.object_correlation(event_1['objects'], event_2['objects'])

                    total_corr = temporal_corr + subject_corr + object_corr

                    correlations.append({
                        'event_1_id': event_1['id'],
                        'event_2_id': event_2['id'],
                        'temporal_correlation': temporal_corr,
                        'subject_correlation': subject_corr,
                        'object_correlation': object_corr,
                        'total_correlation': total_corr
                    })

        correlation_df = pd.DataFrame(correlations)
        return correlation_df

class RelationshipAnalysis:
    def __init__(self, knowledge_representation: KnowledgeRepresentation):
        """
        Initialize analysis helpers for reconstructed relationships.

        :param knowledge_representation: Prepared knowledge representation instance.
        :type knowledge_representation: KnowledgeRepresentation
        """
        self.kr = knowledge_representation
        self.aggregated_correlation_df: pd.DataFrame = pd.DataFrame()

    def sum_correlations(self, correlation_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate total correlation scores by source event ID.

        :param correlation_df: Pairwise correlation DataFrame.
        :type correlation_df: pandas.DataFrame
        :returns: Aggregated correlation DataFrame sorted descending.
        :rtype: pandas.DataFrame
        """
        self.aggregated_correlation_df = (
            correlation_df.groupby("event_1_id", as_index=False)
            .agg({"total_correlation": "sum"})
            .rename(columns={"total_correlation": "total_correlation_sum"})
            .sort_values(by="total_correlation_sum", ascending=False)
            .reset_index(drop=True)
        )
        return self.aggregated_correlation_df

    def filter_events_based_on_avg_correlation(
        self,
        correlation_df: pd.DataFrame,
        timeline_df: pd.DataFrame = None,
        threshold: float = 0.0
    ) -> pd.DataFrame:
        """
        Mark events that pass type-based average correlation filtering.

        Each event is compared to the average ``total_correlation_sum`` of its type.
        A user-defined threshold is added to that average.

        :param correlation_df: Pairwise correlation DataFrame.
        :type correlation_df: pandas.DataFrame
        :param timeline_df: Optional precomputed timeline DataFrame.
        :type timeline_df: pandas.DataFrame or None
        :param threshold: Extra margin added to each type average.
        :type threshold: float
        :returns: Timeline DataFrame with merged scores and boolean ``filter`` column.
        :rtype: pandas.DataFrame
        """
        if self.aggregated_correlation_df.empty:
            self.sum_correlations(correlation_df)

        if timeline_df is None:
            timeline_df = TimelineReconstruction(self.kr).reconstruct_timeline()

        merged_df = timeline_df.merge(
            self.aggregated_correlation_df,
            left_on="id",
            right_on="event_1_id",
            how="left"
        )

        type_means = merged_df.groupby("type")["total_correlation_sum"].transform("mean")
        merged_df["filter"] = (
            merged_df["total_correlation_sum"].fillna(0) >= (type_means.fillna(0) + threshold)
        )

        return merged_df

    def update_timeline_df(self, timeline_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter timeline rows and enrich with subject and object detail metadata.

        :param timeline_df: Timeline DataFrame containing a boolean ``filter`` column.
        :type timeline_df: pandas.DataFrame
        :returns: Filtered and enriched timeline DataFrame.
        :rtype: pandas.DataFrame
        """
        updated_timeline_df = timeline_df[timeline_df["filter"]].copy().reset_index(drop=True)

        cleaned_entities_df = self.kr.cleaned_entities_df
        subject_map = cleaned_entities_df.loc[
            cleaned_entities_df["type"] == "Subject"
        ].set_index("id")["details"]
        object_map = cleaned_entities_df.loc[
            cleaned_entities_df["type"] == "Object"
        ].set_index("id")["details"]

        updated_timeline_df["detail_subject"] = updated_timeline_df["subjects"].map(subject_map)
        updated_timeline_df["detail_object"] = updated_timeline_df["objects"].map(object_map)

        return updated_timeline_df

    def draw_timeline_graph(self, updated_timeline_df: pd.DataFrame, output_path: str = None) -> None:
        """
        Draw a timeline chart grouped by event type.

        :param updated_timeline_df: Filtered timeline DataFrame to plot.
        :type updated_timeline_df: pandas.DataFrame
        :param output_path: Optional file path to save the generated figure.
        :type output_path: str or None
        :returns: None
        :rtype: None
        """
        plt.figure(figsize=(14, 8))

        event_y_positions = {
            event_type: idx for idx, event_type in enumerate(updated_timeline_df["type"].dropna().unique())
        }
        plot_df = updated_timeline_df.copy()
        plot_df["y_position"] = plot_df["type"].map(event_y_positions)

        for _, event in plot_df.iterrows():
            plt.plot(
                [event["time"], event["time"]],
                [event["y_position"] - 0.2, event["y_position"] + 0.2],
                color="blue",
                linewidth=2
            )

        plt.yticks(list(event_y_positions.values()), list(event_y_positions.keys()))
        plt.xlabel("Time")
        plt.ylabel("Event Type")
        plt.title("Filtered Timeline of Incident")
        plt.grid(axis="x")

        if output_path:
            plt.savefig(output_path)
        plt.show()

    def count_classification_groups(self, updated_timeline_df: pd.DataFrame) -> pd.Series:
        """
        Count filtered events by type.

        :param updated_timeline_df: Filtered timeline DataFrame.
        :type updated_timeline_df: pandas.DataFrame
        :returns: Frequency of each event type.
        :rtype: pandas.Series
        """
        return updated_timeline_df["type"].value_counts()

    @staticmethod
    def _build_event_filename_df(event_ids: pd.Series, events_df: pd.DataFrame, footprints_df: pd.DataFrame) -> pd.DataFrame:
        """
        Map event IDs to source filenames through event support IDs.

        :param event_ids: Event ID series.
        :type event_ids: pandas.Series
        :param events_df: Events DataFrame containing ``id`` and ``support``.
        :type events_df: pandas.DataFrame
        :param footprints_df: Footprints DataFrame containing ``id`` and ``filename``.
        :type footprints_df: pandas.DataFrame
        :returns: DataFrame with ``event_1_id`` and resolved ``filename`` columns.
        :rtype: pandas.DataFrame
        """
        supports = event_ids.map(events_df.set_index("id")["support"])
        filenames = supports.map(footprints_df.set_index("id")["filename"])
        return pd.DataFrame({"event_1_id": event_ids, "filename": filenames})

    @staticmethod
    def _resolve_event_id_series(source_df: pd.DataFrame) -> pd.Series:
        """
        Resolve event ID column from a source DataFrame.

        Supports both ``event_1_id`` and ``event1_id`` naming.

        :param source_df: Source DataFrame containing event ID column.
        :type source_df: pandas.DataFrame
        :returns: Event ID series.
        :rtype: pandas.Series
        :raises KeyError: If no supported event ID column exists.
        """
        for candidate in ["event_1_id", "event1_id"]:
            if candidate in source_df.columns:
                return source_df[candidate]
        raise KeyError("Expected one of these columns: 'event_1_id' or 'event1_id'")

    def build_event_summary(
        self,
        events_df: pd.DataFrame,
        footprints_df: pd.DataFrame,
        possible_src_df: pd.DataFrame,
        plausible_src_df: pd.DataFrame
    ) -> tuple:
        """
        Build event summary DataFrames for possible and plausible inferred events.

        :param events_df: Events DataFrame.
        :type events_df: pandas.DataFrame
        :param footprints_df: Footprints DataFrame.
        :type footprints_df: pandas.DataFrame
        :param possible_src_df: Source DataFrame for possible events.
        :type possible_src_df: pandas.DataFrame
        :param plausible_src_df: Source DataFrame for plausible inferred events.
        :type plausible_src_df: pandas.DataFrame
        :returns: Tuple of ``(possible_events_df, plausible_inferred_events_df)``.
        :rtype: tuple
        """
        possible_event_ids = self._resolve_event_id_series(possible_src_df)
        plausible_event_ids = self._resolve_event_id_series(plausible_src_df)

        possible_events_df = self._build_event_filename_df(
            possible_event_ids, events_df, footprints_df
        )
        plausible_inferred_events_df = self._build_event_filename_df(
            plausible_event_ids, events_df, footprints_df
        )

        return possible_events_df, plausible_inferred_events_df

    @staticmethod
    def analyze_fitness_generalization(
        possible_events_df: pd.DataFrame,
        plausible_inferred_events_df: pd.DataFrame,
        files_to_check: List[str] = None
    ) -> pd.DataFrame:
        """
        Compute fitness and generalization metrics globally and per filename.

        :param possible_events_df: DataFrame of candidate possible events.
        :type possible_events_df: pandas.DataFrame
        :param plausible_inferred_events_df: DataFrame of plausible inferred events.
        :type plausible_inferred_events_df: pandas.DataFrame
        :param files_to_check: Optional list of filenames to evaluate individually.
        :type files_to_check: List[str] or None
        :returns: Metrics DataFrame containing global and per-file rows.
        :rtype: pandas.DataFrame
        """
        if files_to_check is None:
            files_to_check = sorted(
                possible_events_df["filename"].dropna().astype(str).unique().tolist()
            )

        total_possible_events = len(possible_events_df)
        total_plausible_inferred_events = len(plausible_inferred_events_df)

        if total_possible_events > 0:
            c_global = total_possible_events - total_plausible_inferred_events
            fitness_global = 1 - c_global / total_possible_events
            generalization_global = total_plausible_inferred_events / total_possible_events
        else:
            fitness_global = 0
            generalization_global = 0

        results = {
            "File": ["All Data"],
            "Fitness": [round(fitness_global, 5)],
            "Generalization": [round(generalization_global, 5)]
        }

        for filename in files_to_check:
            possible_events_filtered = possible_events_df[possible_events_df["filename"] == filename]
            plausible_events_filtered = plausible_inferred_events_df[
                plausible_inferred_events_df["filename"] == filename
            ]

            a = len(possible_events_filtered)
            b = len(plausible_events_filtered)
            c = a - b

            if a > 0:
                fitness = 1 - c / a
                generalization = b / a
            else:
                fitness = 0
                generalization = 0

            results["File"].append(filename)
            results["Fitness"].append(round(fitness, 5))
            results["Generalization"].append(round(generalization, 5))

        return pd.DataFrame(results)


def run_pipeline(
    input_dir: str,
    output_dir: str = None,
    threshold: float = 0.0,
    draw_graph: bool = False,
    graph_filename: str = "filtered_timeline.png"
) -> dict:
    """
    Execute the full reconstruction pipeline from raw CSV files.

    This helper keeps orchestration logic in one place for scripts and CLI use.
    It returns all key intermediate and final DataFrames, and optionally writes
    them to disk in CSV format.

    :param input_dir: Directory containing input CSV files.
    :type input_dir: str
    :param output_dir: Optional directory to save output CSV files.
    :type output_dir: str or None
    :param threshold: Threshold added to type mean in correlation filtering.
    :type threshold: float
    :param draw_graph: Whether to render and optionally save a timeline chart.
    :type draw_graph: bool
    :param graph_filename: Graph filename used when output_dir is provided.
    :type graph_filename: str
    :returns: Dictionary containing generated DataFrames.
    :rtype: dict
    :raises ValueError: If no matching input rows are found.
    """
    processor = DataProcessor(file_dir=input_dir)
    combined_df = processor.process_files()

    if combined_df.empty:
        raise ValueError("No WEBHIST rows were found in input CSV files.")

    kr = KnowledgeRepresentation(combined_df)
    sorted_footprints_df = kr.sort_data()
    kr.extract_entities()

    timeline_builder = TimelineReconstruction(kr)
    timeline_df = timeline_builder.reconstruct_timeline()
    correlation_df = timeline_builder.calculate_correlation(timeline_df)

    analysis = RelationshipAnalysis(kr)
    scored_timeline_df = analysis.filter_events_based_on_avg_correlation(
        correlation_df=correlation_df,
        timeline_df=timeline_df,
        threshold=threshold
    )
    updated_timeline_df = analysis.update_timeline_df(scored_timeline_df)
    classification_counts = analysis.count_classification_groups(updated_timeline_df)

    possible_src_df = scored_timeline_df[["id"]].rename(columns={"id": "event_1_id"})
    plausible_src_df = updated_timeline_df[["id"]].rename(columns={"id": "event_1_id"})

    possible_events_df, plausible_inferred_events_df = analysis.build_event_summary(
        events_df=kr.events_df,
        footprints_df=sorted_footprints_df,
        possible_src_df=possible_src_df,
        plausible_src_df=plausible_src_df
    )

    metrics_df = analysis.analyze_fitness_generalization(
        possible_events_df=possible_events_df,
        plausible_inferred_events_df=plausible_inferred_events_df
    )

    outputs = {
        "combined_filtered": combined_df,
        "sorted_footprints": sorted_footprints_df,
        "cleaned_entities": kr.cleaned_entities_df,
        "events": kr.events_df,
        "support_relationships": kr.support_df,
        "participation": kr.participation_df,
        "usage": kr.usage_df,
        "timeline": timeline_df,
        "correlations": correlation_df,
        "scored_timeline": scored_timeline_df,
        "updated_timeline": updated_timeline_df,
        "possible_events": possible_events_df,
        "plausible_inferred_events": plausible_inferred_events_df,
        "fitness_generalization": metrics_df,
        "classification_counts": classification_counts.rename_axis("type").reset_index(name="count")
    }

    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for name, df in outputs.items():
            if isinstance(df, pd.DataFrame):
                df.to_csv(output_path / f"{name}.csv", index=False)

        if draw_graph:
            analysis.draw_timeline_graph(
                updated_timeline_df,
                output_path=str(output_path / graph_filename)
            )
    elif draw_graph:
        analysis.draw_timeline_graph(updated_timeline_df)

    return outputs

def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argparse parser for the CLI interface.

    :return: Configured argument parser
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Reconformal Pipeline CLI: Event extraction and relationship inference.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-i", "--input-dir",
        type=str,
        required=True,
        help="Directory path containing input CSV files to process."
    )

    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default="reconformal_outputs",
        help="Directory where output CSV files and graphs will be saved."
    )

    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=0.0,
        help="Threshold to apply to the type mean during correlation filtering."
    )

    parser.add_argument(
        "--draw-graph",
        action="store_true",
        help="Whether to generate and save a timeline scatter plot image."
    )

    parser.add_argument(
        "--graph-filename",
        type=str,
        default="filtered_timeline.png",
        help="Custom filename for the output timeline graph (if draw-graph is used)."
    )

    return parser

def main():
    """
    Entry point for CLI execution.
    """
    parser = create_parser()
    args = parser.parse_args()

    try:
        print(f"Starting pipeline with input directory: {args.input_dir}")
        outputs = run_pipeline(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            threshold=args.threshold,
            draw_graph=args.draw_graph,
            graph_filename=args.graph_filename
        )
        print("Pipeline execution completed successfully.")
        print(f"Generated {len(outputs)} dataframes.")
        if args.output_dir:
            print(f"Outputs written to: {args.output_dir}")
    except Exception as e:
        print(f"Error during execution: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
