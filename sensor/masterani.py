REQUIREMENTS = ['requests==2.19.1']

from datetime import date, timedelta
from homeassistant.helpers.entity import Entity

SCAN_INTERVAL = timedelta(minutes=1)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    add_devices([AnimeSensor(id) for id in config['ids']])

def _get_json(url):
    import requests
    r = requests.get(url)
    return r.json()

def _get_detailed(id):
    return _get_json('https://www.masterani.me/api/anime/{}/detailed'.format(id))

class CombinedAnimeSensor(Entity):
    pass

class AnimeSensor(Entity):
    def __init__(self, id):
        self.id = id
        self._data = None
        self._cover = None
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        if self._data:
            return self.device_state_attributes['title']
        else:
            return 'Masterani #{}'.format(self.id)

    @property
    def entity_id(self):
        return 'sensor.masterani_{}'.format(self.id)

    @property
    def state(self):
        if self._data:
            return None
            #return self.device_state_attributes['last_episode']
        else:
            return None

    @property
    def unit_of_measurement(self):
        return 'ep'

    @property
    def icon(self):
        return 'mdi:filmstrip'
    
    @property
    def entity_picture(self):
        return self._cover

    @property
    def device_state_attributes(self):
        if self._data:
            d = self._data['info']
            e = self._data['episodes'][-1]
            return {
                'title': d['title'],
                'episodes': d['episode_count'],
                #'last_episode': e['episode'],
                #'last_episode_title': e['title'],
            }
        else:
            return { }

    def update(self):
        self._data = _get_detailed(self.id)
        print(self._data)
        print(self._data['episodes'][-1])

        if self._data['poster']:
            self._cover = 'https://cdn.masterani.me/poster/3/{}'.format(self._data['poster'])
