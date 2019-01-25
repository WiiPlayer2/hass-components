REQUIREMENTS = ['fints==0.2.1']

from datetime import date, timedelta
from homeassistant.helpers.entity import Entity

SCAN_INTERVAL = timedelta(minutes=15)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    from fints.client import FinTS3PinTanClient
    client = FinTS3PinTanClient(str(config['blz']), str(config['username']), str(config['pin']), str(config['endpoint']))
    add_devices([FintsSensor(client, account) for account in client.get_sepa_accounts()])


class FintsSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, client, account):
        """Initialize the sensor."""
        self._client = client
        self._account = account
        self._state = None
        self._lastStmt = None
        self._balance = 0
        self._pendingBalance = 0
        self._pendingValue = 0
        self._pendingStmt = None
        self._entityId = 'sensor.fints_{}'.format(self._account.iban).lower()
        # self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Account {}'.format(self._account.iban)

    @property
    def entity_id(self):
        return self._entityId

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._balance.amount

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._balance.currency

    @property
    def device_state_attributes(self):
        stmt = self._lastStmt
        pend = self._pendingStmt
        if stmt:
            return {
                'pending_balance': float(self._pendingBalance),
                'pending_total_value': float(self._pendingValue),
                'pending_date': (pend or None) and pend.data['date'].isoformat(),
                'pending_value': (pend or None) and float(pend.data['amount'].amount),
                'pending_applicant': (pend or None) and pend.data['applicant_name'],
                'pending_purpose': (pend or None) and pend.data['purpose'],
                'last_date': stmt.data['date'].isoformat(),
                'last_value': float(stmt.data['amount'].amount),
                'last_applicant': stmt.data['applicant_name'],
                'last_purpose': stmt.data['purpose']
            }
        else:
            return {}
    
    @property
    def icon(self):
        return 'mdi:bank'

    def is_pending_stmt(self, stmt):
        if stmt.data['amount'].amount > 0:
            return False
        return stmt.data['date'] != stmt.data['entry_date'] or stmt.data['applicant_name'] is None

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        stmt = None
        stmts = self._client.get_statement(self._account, date.today() - timedelta(weeks=2), date.today())

        markedValue = 0
        index = -1
        while index >= -(len(stmts)) and self.is_pending_stmt(stmts[index]) :
            markedValue += stmts[index].data['amount'].amount
            index -= 1
        if len(stmts) + index >= 0:
            stmt = stmts[index]
        elif len(stmts) > 0:
            stmt = stmts[-1]

        if len(stmts) > 0:
            self._pendingStmt = stmts[-1]
        if stmt == self._pendingStmt:
            self._pendingStmt = None

        self._balance = self._client.get_balance(self._account).amount
        self._pendingValue = markedValue
        self._pendingBalance = self._balance.amount + markedValue
        self._lastStmt = stmt
