# honepad: bank_system
# saved: 2026-10-30 23:47
# ---
from dataclasses import dataclass,field
@dataclass
class Account:
    id: str
    balance:int = 0
    time:int = 0
    out:int = 0
    history:list = field(default_factory=list)

@dataclass
class Payment:
    id: str
    due: int
    amount: int
    status: str = "IN_PROGRESS"
class Simulation:
    from collections import defaultdict
    def __init__(self):
        self.acnt = self.defaultdict(Account)
        self.pmt = self.defaultdict(Payment)
        self.N = 1
    def create_account(self, timestamp, account_id):
        """Create an account. True if created, false if the id exists."""
        self._cashback(timestamp=timestamp)
        if account_id in self.acnt:
            return False
        self.acnt[account_id] = Account(account_id,time=timestamp)
        acc = self.acnt[account_id]
        self.acnt[account_id].history.append((timestamp,acc.balance))
        return True
        # raise NotImplementedError

    def deposit(self, timestamp, account_id, amount):
        """Add funds. New balance, or None if the account is missing."""
        self._cashback(timestamp=timestamp)
        if account_id not in self.acnt:
            return None
        acc = self.acnt[account_id]
        acc.balance += amount
        acc.time = timestamp
        acc.history.append((timestamp,acc.balance))
        return acc.balance
        # raise NotImplementedError

    def transfer(self, timestamp, source_account_id, target_account_id, amount):
        """Move funds. Source balance, or None if missing, same, or broke."""
        self._cashback(timestamp=timestamp)
        if source_account_id == target_account_id or source_account_id not in self.acnt or target_account_id not in self.acnt:
            return None
        if self.acnt[source_account_id].balance < amount:
            return None
        accs = self.acnt[source_account_id]
        acct = self.acnt[target_account_id]
        accs.balance -= amount
        accs.history.append((timestamp,accs.balance))
        accs.out += amount
        accs.time = timestamp
        acct.balance += amount
        acct.history.append((timestamp,acct.balance))
        acct.time = timestamp
        return accs.balance

    def top_spenders(self, timestamp, n):
        """Top accounts as id(outgoing). Incoming does not count.

        Example: ["acc1(500)", "acc2(0)"].
        """
        self._cashback(timestamp=timestamp)
        result = sorted(self.acnt.values(), key = lambda x: (-x.out,x.id))
        ans = []
        for acc in result:
            ans.append(f"{acc.id}({acc.out})")
        return ans[:n]

    def get_payment_status(self, timestamp, account_id, payment):
        """IN_PROGRESS or CASHBACK_RECEIVED, or None if wrong."""
        self._cashback(timestamp=timestamp)
        if account_id not in self.acnt:
            return None
        if payment not in self.pmt:
            return None
        if self.pmt[payment].id != account_id:
            return None
        return "IN_PROGRESS" if self.pmt[payment].due>timestamp else "CASHBACK_RECEIVED"
        

    def pay(self, timestamp, account_id, amount):
        """Withdraw now. Returns paymentN, or None.

        Example: "payment1".
        """
        self._cashback(timestamp=timestamp)
        if account_id not in self.acnt:
            return None
        acc = self.acnt[account_id]
        if acc.balance < amount:
            return None
        acc.balance -= amount
        acc.out += amount
        acc.history.append((timestamp,acc.balance))
        self.pmt[f"payment{self.N}"] = Payment(account_id,amount=amount,due=timestamp+86400000)
        self.N += 1
        return f"payment{self.N-1}"

    def _cashback(self,timestamp):
        for pmt in self.pmt.values():
            if pmt.due <= timestamp and pmt.status == "IN_PROGRESS":
                id = pmt.id
                self.acnt[id].balance += (pmt.amount*2//100)
                self.acnt[id].history.append((pmt.due, self.acnt[id].balance))
                pmt.status = "CASHBACK_RECEIVED"

    def get_balance(self, timestamp, account_id, time_at):
        """Balance at time_at after cashbacks due at timestamp."""
        self._cashback(timestamp=timestamp)
        if account_id not in self.acnt:
            return None
        acc = self.acnt[account_id]
        left,right = 0,len(acc.history)-1
        while left <= right:
            mid = (left+right)//2
            if acc.history[mid][0] <= time_at:
                left = mid+1
            else:
                right = mid-1
        return acc.history[right][1] if right >= 0 else None

    def merge_accounts(self, timestamp, account_id_1, account_id_2):
        """Merge account_id_2 into account_id_1, then delete account_id_2.

        Moves balance, outgoing, payments, history, and pending cashbacks.
        False if either id is missing or they are the same.
        """
        self._cashback(timestamp=timestamp)
        if account_id_1 not in self.acnt or account_id_2 not in self.acnt or account_id_1 == account_id_2:
            return False
        keep = self.acnt[account_id_1]
        drop = self.acnt[account_id_2]
        keep.balance += drop.balance
        keep.out += drop.out
        keep.history.append((timestamp,keep.balance))
        keep.history = sorted(keep.history+drop.history, key= lambda x:x[0])
        del self.acnt[account_id_2]
        for pmt in self.pmt.values():
            if pmt.id == account_id_2:
                pmt.id = account_id_1
        return True

