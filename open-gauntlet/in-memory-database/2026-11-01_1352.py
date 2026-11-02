# open-gauntlet: in-memory-database
# started: 2026-11-01 13:52
# completed levels: [1, 2, 3, 4] (finished)
# finished at (elapsed): L1 6:28, L2 12:45, L3 25:09, L4 45:37
# ---
from dataclasses import dataclass
from bisect import bisect_right
@dataclass
class Store:
    key: str
    record: dict

@dataclass
class Record:
    key: str
    field: str
    value: str
    due: float= float("inf")
class InMemoryDatabase:
    """A key-field-value store. Records are identified by a string key,
    each holding multiple (field, value) pairs."""

    def __init__(self):
        self.db = {}
        self.backups = []

    def set(self, key: str, field: str, value: str):
        """Insert or update a field in the record at key. Returns None."""
        record = {}
        if key in self.db:
            record = self.db[key].record
        record[field] = Record(key=key,field=field,value=value)
        self.db[key] = Store(key=key,record=record)
        return None

    def get(self, key: str, field: str):
        """Return the value of field in the record at key. Returns None if not found."""
        if key not in self.db:
            return None
        store = self.db[key]
        if field not in store.record:
            return None
        return store.record[field].value

    def delete(self, key: str, field: str) -> bool:
        """Remove field from the record at key. Returns True if deleted, False if not found."""
        if key not in self.db:
            return False
        store = self.db[key]
        if field not in store.record:
            return False
        self.db[key].record.pop(field)
        return True


    def scan(self,key):
        if key not in self.db:
            return ""
        store = self.db[key]
        ans = []
        for field,rcd in store.record.items():
            ans.append(f"{field}({rcd.value})")
        return ", ".join(sorted(ans))
    
    def scan_by_prefix(self,key, prefix):
        if key not in self.db:
            return ""
        store = self.db[key]
        ans = []
        for field,rcd in store.record.items():
            if field.startswith(prefix):
                ans.append(f"{field}({rcd.value})")
        return ", ".join(sorted(ans))

    def set_at(self,key, field, value, timestamp):
        self.set(key,field,value)
    
    def set_at_with_ttl(self,key, field, value, timestamp, ttl):
        record = {}
        if key in self.db:
            record = self.db[key].record
        record[field] = Record(key=key,field=field,value=value,due=timestamp+ttl)
        self.db[key] = Store(key=key,record=record)

    def get_at(self,key, field, timestamp):
        if key not in self.db:
            return None
        store = self.db[key]
        if field not in store.record:
            return None
        rcd = store.record[field]
        if rcd.due > timestamp:
            return rcd.value
        return None

    def delete_at(self, key, field, timestamp):
        if key not in self.db:
            return False
        store = self.db[key]
        if field not in store.record:
            return False
        rcd = store.record[field]
        if rcd.due <= timestamp:
            return False
        self.db[key].record.pop(field)
        return True
    
    def scan_at(self,key, timestamp):
        if key not in self.db:
            return ""
        store = self.db[key]
        ans = []
        for field,rcd in store.record.items():
            if rcd.due > timestamp:
                ans.append(f"{field}({rcd.value})")
        return ", ".join(sorted(ans))

    def scan_by_prefix_at(self,key, prefix,timestamp):
        if key not in self.db:
            return ""
        store = self.db[key]
        ans = []
        for field,rcd in store.record.items():
            if field.startswith(prefix) and rcd.due > timestamp:
                ans.append(f"{field}({rcd.value})")
        return ", ".join(sorted(ans))

    def backup(self,timestamp):
        snapshot = {}
        for key,store in self.db.items():
            record = {}
            for rcd in store.record.values():
                if rcd.due > timestamp:
                    record[rcd.field] = Record(key=key,field=rcd.field,
                                        value=rcd.value,due=rcd.due-timestamp)
            if record:
                snapshot[key] = Store(key=key,record=record)
        self.backups.append((timestamp,snapshot))
        return len(snapshot)

    def restore(self, timestamp, timestamp_to_restore):
        idx = bisect_right(self.backups,timestamp_to_restore,key=lambda x:x[0])-1
        if idx<0 or idx>len(self.backups)-1:
            return None
        _,snapshot = self.backups[idx]
        for store in snapshot.values():
            for rcd in store.record.values():
                remain = rcd.due
                rcd.due = timestamp+remain
        self.db = snapshot
        return None





