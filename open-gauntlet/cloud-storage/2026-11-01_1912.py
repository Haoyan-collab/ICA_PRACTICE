# open-gauntlet: cloud-storage
# started: 2026-11-01 19:12
# completed levels: [1, 2, 3, 4] (finished)
# finished at (elapsed): L1 3:00, L2 13:40, L3 39:00, L4 52:25
# ---
from dataclasses import dataclass,field
@dataclass
class File:
    name: str
    size: int

@dataclass
class User:
    id: str
    capacity: int=0
    space: int=0
    files: dict = field(default_factory=dict)
class CloudStorage:
    """A flat file storage system. Files have names and sizes,
    all sharing a single namespace."""

    def __init__(self):
        self.file_db = {}
        self.user_db = {}
    def add_file(self, name: str, size: int) -> bool:
        """Add a file. Returns True if added, False if name already exists."""
        if name in self.file_db:
            return False
        self.file_db[name] = File(name=name,size=size)
        return True

    def get_file_size(self, name: str):
        """Return file size as integer, or None if not found."""
        if name not in self.file_db:
            return None
        return self.file_db[name].size

    def copy_file(self, name_from: str, name_to: str) -> bool:
        """Copy a file. Returns True on success, False if source doesn't exist."""
        if name_from not in self.file_db:
            return False

        self.file_db[name_to] = File(name=name_to,size=self.get_file_size(name_from))
        return True

    def find_file(self, prefix, suffix):
        ans = []
        print(self.file_db)
        for file in sorted(self.file_db.values(),key=lambda x:(-x.size,x.name)):
            if file.name.startswith(prefix) and file.name.endswith(suffix):
                ans.append(file.name)
        return ans[:10]

    def add_user(self, user_id, capacity):
        if user_id in self.user_db:
            return False
        self.user_db[user_id] = User(id=user_id,capacity=capacity,space=capacity)
        return True

    def add_file_by(self, user_id, name, size):
        if user_id not in self.user_db:
            return None
        user = self.user_db[user_id]
        if name in user.files or name in self.file_db or size > user.space:
            return None
        user.files[name] = File(name=name,size=size)
        user.space -= size
        self.file_db[name] = File(name=name,size=size)
        return user.space
    
    def update_capacity(self, user_id, new_capacity):
        if user_id not in self.user_db:
            return None
        user = self.user_db[user_id]
        usage = user.capacity-user.space
        if new_capacity < usage:
            for file in sorted(user.files.values(),key=lambda x:(x.size,x.name),reverse = True):
                user.files.pop(file.name)
                self.file_db.pop(file.name)
                usage -= file.size
                if usage <= new_capacity:
                    break
        user.capacity = new_capacity
        user.space = new_capacity-usage
        return user.space

    def compress_file(self, user_id, name):
        if user_id not in self.user_db:
            return None
        user = self.user_db[user_id]
        if name not in user.files or name.endswith(".compressed"):
            return None
        file = user.files[name]
        c_file = File(name=f"{name}.compressed",size=file.size//2)
        user.space += file.size - c_file.size
        user.files.pop(name)
        user.files[c_file.name] = c_file
        self.file_db.pop(name)
        self.file_db[c_file.name] = c_file
        return user.space
    
    def decompress_file(self, user_id, name):
        if user_id not in self.user_db:
            return None
        user = self.user_db[user_id]
        if name not in user.files or not name.endswith(".compressed") or name[:-len(".compressed")] in user.files:
            return None
        file = user.files[name]
        dc_file = File(name=file.name[:-len(".compressed")],size=file.size*2)
        need = dc_file.size - file.size
        if need > user.space:
            return None
        user.space -= need
        user.files[dc_file.name] = dc_file
        self.file_db.pop(name)
        self.file_db[dc_file.name] = dc_file
        return user.space



















