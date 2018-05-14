REQUIREMENTS = ['fints==0.2.1']

from datetime import date, timedelta
from fints.client import FinTS3PinTanClient
from homeassistant.helpers.entity import Entity

SCAN_INTERVAL = timedelta(minutes=15)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
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
        self._markedBalance = 0
        self._markedValue = 0
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Account {}'.format(self._account.iban)

    @property
    def entity_id(self):
        return 'sensor.fints_{}'.format(self._account.iban)

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
        if stmt:
            return {
                'marked_balance': float(self._markedBalance),
                'marked_value': float(self._markedValue),
                'date': stmt.data['date'].isoformat(),
                'value': float(stmt.data['amount'].amount),
                'applicant': stmt.data['applicant_name'],
                'purpose': stmt.data['purpose']
            }
        else:
            return {}
    
    @property
    def icon(self):
        return 'mdi:bank'

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        stmt = None
        stmts = self._client.get_statement(self._account, date.today() - timedelta(weeks=2), date.today())

        markedValue = 0
        index = -1
        while index >= -(len(stmts)) and stmts[index].data['date'] != stmts[index].data['entry_date'] :
            markedValue += stmts[index].data['amount'].amount
            index -= 1
        if len(stmts) + index >= 0:
            stmt = stmts[index]
        elif len(stmts) > 0:
            stmt = stmts[-1]

        self._balance = self._client.get_balance(self._account).amount
        self._markedValue = markedValue
        self._markedBalance = self._balance.amount + markedValue
        self._lastStmt = stmt
