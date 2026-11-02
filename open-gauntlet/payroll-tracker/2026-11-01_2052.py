# open-gauntlet: payroll-tracker
# started: 2026-11-01 20:52
# completed levels: [1, 2, 3, 4] (finished)
# finished at (elapsed): L1 11:04, L2 13:28, L3 49:05, L4 65:08
# ---
from dataclasses import dataclass,field
@dataclass
class Worker:
    id:str
    position:str
    compensation:int=0
    total_time: int=0
    record: list = field(default_factory=list)
    rate: list=field(default_factory=list)

class PayrollTracker:
    """Track worker check-in/check-out times and compute hours worked."""

    def __init__(self):
        self.worker_db = {}
        self.double = []
    def add_worker(self, worker_id: str, position: str, compensation: int) -> bool:
        """Register a new worker. Returns True if added, False if already exists."""
        if worker_id in self.worker_db:
            return False
        self.worker_db[worker_id] = Worker(id=worker_id,position=position,compensation=compensation,rate=[(0,compensation)])
        return True

    def register(self, worker_id: str, timestamp: int) -> str:
        """Record entry/exit event. Returns 'registered' or None if not found."""
        if worker_id not in self.worker_db:
            return None
        worker = self.worker_db[worker_id]
        if len(worker.record)%2 == 0:
            worker.record.append(timestamp)
        else:
            worker.total_time += timestamp-worker.record[-1]
            worker.record.append(timestamp)
        return 'registered'
        

    def get_total(self, worker_id: str):
        """Return total time in office as integer, or None if not found."""
        if worker_id not in self.worker_db:
            return None
        worker = self.worker_db[worker_id]
        return worker.total_time

    def top_workers(self,n):
        ans = []
        for worker in sorted(self.worker_db.values(),key=lambda x:(-x.total_time,x.id)):
            ans.append(f"{worker.id}({worker.total_time})")
            if len(ans) == n:
                break
        return ans

    def promote(self,worker_id, timestamp, position, compensation):
        if worker_id not in self.worker_db:
            return None
        worker = self.worker_db[worker_id]
        worker.rate.append((timestamp,compensation))
        worker.position = position
        worker.compensation = compensation
        return True
    
    def get_salary(self,worker_id, start_ts, end_ts):
        if worker_id not in self.worker_db:
            return None
        worker = self.worker_db[worker_id]
        salary = 0
        for i in range(0,len(worker.record)-1,2):
            w_start = worker.record[i]
            w_end = worker.record[i+1]
            for j in range(len(worker.rate)):
                r_start,compensation = worker.rate[j]
                r_end = worker.rate[j+1][0] if j+1<len(worker.rate) else float("inf")
                l = max(w_start,r_start,start_ts)
                r = min(w_end,r_end,end_ts)
                if l<r:
                    salary += (r-l)*compensation
                    for start,end in self.double:
                        d_start = max(start,l)
                        d_end = min(end,r)
                        if d_start < d_end:
                            salary += (d_end-d_start)*compensation
        return salary
    
    def set_double_paid(self,start_ts, end_ts):
        self.double.append((start_ts,end_ts))
        merged = []
        for start,end in self.double:
            if not merged or start>merged[-1][1]:
                merged.append((start,end))
            else:
                merged[-1] = (min(merged[-1][0],start),max(merged[-1][1],end))
        self.double = merged
        return None


















































