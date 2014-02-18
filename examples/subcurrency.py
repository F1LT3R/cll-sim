from sim import Contract, Simulation, Tx, log, stop

class SubCurrency(Contract):
    """Sub-currency contract example from https://github.com/ethereum/wiki/wiki/%5BEnglish%5D-White-Paper#wiki-sub-currencies"""

    def run(self, tx, contract, block):
        if tx.value < 100 * block.basefee:
            stop("Insufficient fee")
        elif contract.storage[1000]:
            frm = tx.sender
            to = tx.data[0]
            value = tx.data[1]
            if to <= 1000:
                stop("Data[0] 'to' out of bounds: %s" % to)
            if contract.storage[frm] < value:
                stop("Insufficient funds, %s has %d needs %d" % (tx.sender, contract.storage[frm], value))
            log("Transfering %d from %s to %s" % (value, frm, to))
            contract.storage[frm] = contract.storage[frm] - value
            contract.storage[to] = contract.storage[to] + value
        else:
            log("Initializing storage for creator %s" % self.MYCREATOR)
            contract.storage[self.MYCREATOR] = 10 ** 18
            contract.storage[1000] = 1


class SubCurrencyRun(Simulation):

    contract = SubCurrency(MYCREATOR="alice")

    def test_insufficient_fee(self):
        tx = Tx(sender='alice', value=10)
        self.run(tx, self.contract)
        assert self.stopped == 'Insufficient fee'

    def test_creation(self):
        tx = Tx(sender='alice', value=100)
        self.run(tx, self.contract)
        assert self.contract.storage['alice'] == 10 ** 18

    def test_alice_to_bob(self):
        tx = Tx(sender='alice', value=100, data=['bob', 1000])
        self.run(tx, self.contract)
        assert self.contract.storage['alice'] == 10 ** 18 - 1000
        assert self.contract.storage['bob'] == 1000

    def test_bob_to_charlie_invalid(self):
        tx = Tx(sender='bob', value=100, data=['charlie', 1001])
        self.run(tx, self.contract)
        assert self.stopped == 'Insufficient funds, bob has 1000 needs 1001'
        assert self.contract.storage['bob'] == 1000
        assert self.contract.storage['charlie'] == 0

    def test_bob_to_charlie_valid(self):
        tx = Tx(sender='bob', value=100, data=['charlie', 1000])
        self.run(tx, self.contract)
        assert self.contract.storage['bob'] == 0
        assert self.contract.storage['charlie'] == 1000

    def test_storage_result(self):
        self.log(self.contract.storage)
