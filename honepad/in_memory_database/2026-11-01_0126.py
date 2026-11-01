# honepad: in_memory_database
# saved: 2026-11-01 01:26
# ---
from dataclasses import dataclass,field as dc_field
from bisect import bisect_right
@dataclass
class Field:
    name: str
    value: str
    due: float= float("inf")
    status: str= "valid"

@dataclass
class db:
    key: str
    field: dict
    

class InMemoryDatabase:

    def __init__(self):
        self.db = {}
        self.backups = []

    def set(self, key, field, value):
        """Write a field. Returns ""."""

        if key in self.db:
            cur = self.db[key]
            cur.field[field] = Field(name=field,value=value)
            
        else:
            fd = Field(name=field,value=value)
            self.db[key] = db(key=key,field={field:fd})
        return ""

    def get(self, key, field):
        """Value, or "" if missing."""
        if key not in self.db:
            return ""
        cur = self.db[key]
        if field not in cur.field:
            return ""
        return cur.field[field].value

    def delete(self, key, field):
        """Returns "true" if deleted, "false" if missing."""
        if key not in self.db:
            return "false"
        cur = self.db[key]
        if field not in cur.field:
            return "false"
        self.db[key].field.pop(field)
        return "true"

    def scan(self, key):
        """Fields as field(value), ... sorted by field. Empty if none.

        Example: "abc(123), age(30), city(NY), name(Alice)".
        """
        if key not in self.db:
            return ""
        cur = self.db[key]
        ans = []
        for f,v in sorted(cur.field.items()):
            ans.append(f"{f}({v.value})")
        return ", ".join(ans)

    def scan_by_prefix(self, key, prefix):
        """Same as scan, only fields starting with prefix.

        Example: "abc(123), age(30)".
        """
        if key not in self.db:
            return ""
        cur = self.db[key]
        ans = []
        for f,v in sorted(cur.field.items()):
            if f.startswith(prefix):
                ans.append(f"{f}({v.value})")
        return ", ".join(ans)

    def delete_at(self, key, field, timestamp):
        """Delete if live at timestamp. "true" or "false"."""
        if key not in self.db:
            return "false"
        cur = self.db[key]
        if field not in cur.field:
            return "false"
        fd = cur.field[field]
        if fd.due > timestamp:
            cur.field.pop(field)
            return "true"
        return "false"
    
    def get_at(self, key, field, timestamp):
        """Value if live at timestamp, else ""."""
        if key not in self.db:
            return ""
        cur = self.db[key]
        if field not in cur.field:
            return ""
        fd = cur.field[field]
        if fd.due > timestamp:
            return fd.value
        else:
            return ""

    def scan_at(self, key, timestamp):
        """Live fields at timestamp as field(value), ..., or ""."""
        if key not in self.db:
            return ""
        cur = self.db[key]
        ans = []
        for f in cur.field.values():
            if f.due <= timestamp:
                continue
            ans.append(f"{f.name}({f.value})")
        return ", ".join(sorted(ans))

    def scan_by_prefix_at(self, key, prefix, timestamp):
        """Live fields with that prefix at timestamp, or ""."""
        if key not in self.db:
            return ""
        cur = self.db[key]
        ans = []
        for f in cur.field.values():
            if f.due <= timestamp:
                continue
            if f.name.startswith(prefix):
                ans.append(f"{f.name}({f.value})")
        return ", ".join(sorted(ans))

    def set_at(self, key, field, value, timestamp):
        """Write with no expiry. Timestamp is not stored. Returns ""."""
        self.set(key,field,value)
        return ""

    def set_at_with_ttl(self, key, field, value, timestamp, ttl):
        """Write live in [timestamp, timestamp + ttl). Returns ""."""
        if key in self.db:
            cur = self.db[key]
            cur.field[field] = Field(name=field,value=value,due=timestamp+ttl)
            
        else:
            fd = Field(name=field,value=value,due=timestamp+ttl)
            self.db[key] = db(key=key,field={field:fd})

        return ""

    def backup(self, timestamp):
        """Snapshot live keys. Key count as a string."""
        snapshot = {}
        for v in self.db.values():
            fields = {}
            for f in v.field.values():
                if f.due > timestamp:
                    fields[f.name] = (f.value,f.due - timestamp)
            if fields:
                snapshot[v.key] = fields
        self.backups.append((timestamp,snapshot))
        return str(len(snapshot))

    def restore(self, timestamp, timestamp_to_restore):
        """Copy latest backup at or before timestamp_to_restore. Returns ""."""
        idx = bisect_right(self.backups,timestamp_to_restore,key= lambda x:x[0])
        idx -= 1
        if idx<0 or idx>len(self.backups)-1:
            return ""
        _,snapshot = self.backups[idx]
        restored = {}

        for key,fds in snapshot.items():
            fields = {}
            for name,(value,remain) in fds.items():
                fields[name] = Field(name=name,value=value,due=timestamp+remain)
            restored[key] = db(key=key,field=fields)

        self.db = restored
        return ""