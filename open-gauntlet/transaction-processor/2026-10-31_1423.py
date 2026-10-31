# open-gauntlet: transaction-processor
# started: 2026-10-31 14:23
# completed levels: [1, 2, 3, 4] (finished)
# finished at (elapsed): L1 7:37, L2 14:30, L3 30:55, L4 80:29
# ---
from dataclasses import dataclass, field
from bisect import bisect_right
@dataclass
class Account:
    id: str
    balance: float = 0
    out: float = 0
    history: list = field(default_factory = list)

@dataclass
class Payment:
    pid: str
    from_id: str
    to_id: str
    scheduled_at: int= 0
    amount: int= 0
    status: str= "pending"

class TransactionProcessor:
    """Bank account management system with transfers and balance tracking."""

    def __init__(self):
        self.acnt = {}
        self.N = 0
        self.pmt = {}
        self.merged = {}
    def create_account(self, account_id: str, initial_balance: float = 0) -> bool:
        """Create a new account. Returns True if created, False if already exists."""
        if account_id in self.acnt:
            return False
        self.acnt[account_id] = Account(account_id,balance= initial_balance)
        self._record_change(account_id=account_id,balance=initial_balance)
        return True

    def deposit(self, account_id: str, amount: float, timestamp=None) -> float | None:
        """Add amount to balance. Returns new balance, or None if account not found."""
        self._process_payment(timestamp)
        if account_id not in self.acnt:
            return None
        acc = self.acnt[account_id]
        acc.balance += amount
        self._record_change(timestamp,acc.id,acc.balance)
        return acc.balance

    def transfer(self, from_id: str, to_id: str, amount: float, timestamp=None) -> bool | None:
        """Transfer between accounts. Returns True if successful, False if insufficient funds, None if account not found."""
        self._process_payment(timestamp)
        if from_id not in self.acnt or to_id not in self.acnt or from_id == to_id:
            return None
        acc1 = self.acnt[from_id]
        acc2 = self.acnt[to_id]
        if acc1.balance < amount:
            return False
        acc1.balance -= amount
        self._record_change(timestamp,acc1.id,acc1.balance)
        acc1.out += amount
        acc2.balance += amount
        self._record_change(timestamp,acc2.id,acc2.balance)
        return True

    def get_balance(self, account_id: str) -> float | None:
        """Return current balance, or None if account not found."""
        if account_id not in self.acnt:
            return None
        return self.acnt[account_id].balance


    def top_spenders(self,n):
        """Return the top n accounts ranked by total outgoing transfer volume (sum of all successful outbound transfer calls), in descending order."""
        rank = sorted(self.acnt.values(), key= lambda x:(-x.out,x.id))
        ans = []
        for r in rank:
            ans.append(f"{r.id}({r.out})")
        return ans[:n]


    def schedule_payment(self,from_id, to_id, amount, scheduled_at):
        """Schedule a transfer of amount from from_id to to_id that executes at timestamp scheduled_at. Return a unique payment ID (e.g. "payment_0", "payment_1"). Return None if either account doesn't exist."""
        if from_id not in self.acnt or to_id not in self.acnt:
            return None
        pid = f"payment_{self.N}"
        self.pmt[pid] = Payment(pid=pid,from_id=from_id,to_id=to_id,amount=amount,scheduled_at=scheduled_at)
        self.N += 1
        return pid
        

    def cancel_payment(self,payment_id):
        """Cancel a pending payment before it fires. Return True if cancelled. Return False if the ID doesn't exist or the payment already executed."""
        if payment_id not in self.pmt:
            return False
        p = self.pmt[payment_id]
        if p.status != "pending":
            return False
        p.status = "cancelled"
        return True


    def merge_accounts(self, account_id1, account_id2):
        """Return True on success. Return None if either account doesn't exist. Return False if both IDs are the same."""
        if account_id1 not in self.acnt or account_id2 not in self.acnt:
            return None
        if account_id1 == account_id2:
            return False
        acc1 = self.acnt[account_id1]
        acc2 = self.acnt[account_id2]
        acc1.balance += acc2.balance
        self.merged[account_id2] = acc2
        self.acnt.pop(account_id2)
        # self._record_change()
        # process payment
        for p in self.pmt.values():
            if p.status == "pending":
                if p.from_id == account_id2:
                    self.pmt[p.pid] = None
                elif p.to_id == account_id2:
                    p.to_id = account_id1
        return True

    def get_balance_at(self,account_id, time_at):
        """Return the balance of account_id at the given past timestamp time_at. Reconstruct from transaction history: sum all transactions that occurred at or before time_at. 
        Return None if the account has never existed (including accounts that were merged away). If querying a merged account's history before the merge timestamp, return the balance it had at that time. If querying after the merge timestamp, the account no longer exists — return None."""
        if account_id not in self.acnt and account_id not in self.merged:
            return None
        if account_id in self.acnt:
            acc = self.acnt[account_id]
        else:
            acc = self.merged[account_id]
        idx = bisect_right(acc.history,time_at,key= lambda x:x[0])
        idx -= 1
        if idx<0 or idx>len(acc.history)-1:
            return None
        return acc.history[idx][1]


    def _process_payment(self,timestamp=None):
        for p in self.pmt.values():
            if p.scheduled_at <= timestamp and p.status == "pending":
                # do the transfer
                acc1 = self.acnt[p.from_id]
                acc2 = self.acnt[p.to_id]
                if acc1.balance >= p.amount:
                    acc1.balance -= p.amount
                    self._record_change(timestamp,acc1.id,acc1.balance)
                    acc1.out += p.amount
                    acc2.balance += p.amount
                    self._record_change(timestamp,acc2.id,acc2.balance)
                    # change payment status
                    p.status = "executed"
                else:
                    p.status = "failed"

    def _record_change(self,timestamp=0,account_id=None,balance=None):
        acc = self.acnt[account_id]
        acc.history.append((timestamp,balance))
