REQUIREMENTS = ['requests==2.19.1']

from datetime import date, timedelta
from homeassistant.helpers.entity import Entity

SCAN_INTERVAL = timedelta(minutes=1)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    add_devices([AnimeSensor(id) for id in config['ids']])
    add_devices([CombinedAnimeSensor([str(id) for id in config['ids']])])

def _get_json(url):
    import requests
    r = requests.get(url)
    return r.json()

def _get_detailed(id):
    return _get_json('https://www.masterani.me/api/anime/{}/detailed'.format(id))

def _get_releases():
    return _get_json('https://www.masterani.me/api/releases')

class CombinedAnimeSensor(Entity):
    def __init__(self, ids):
        self._ids = ids
        self._data = None
        self._cover = None
        self.update()
    
    @property
    def name(self):
        return 'Masterani'
    
    @property
    def entity_id(self):
        return 'sensor.masterani'
    
    @property
    def state(self):
        if self._data:
            return '{} #{}'.format(self._data['anime']['title'], self._data['episode'])
        else:
            return None
    
    @property
    def device_state_attributes(self):
        if self._data:
            a = self._data['anime']
            return {
                'id': a['id'],
                'title': a['title'],
                'episode': self._data['episode'],
            }
        else:
            return { }
    
    @property
    def icon(self):
        return 'mdi:filmstrip'
    
    @property
    def entity_picture(self):
        return self._cover

    def update(self):
        releases = _get_releases()
        for r in releases:
            if str(r['anime']['id']) in self._ids:
                self._data = r
                self._cover = 'https://cdn.masterani.me/poster/3/{}'.format(self._data['anime']['poster'])
                break

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
            return self.device_state_attributes['last_episode']
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
            e = self._data['episodes'][-1]['info']
            return {
                'title': d['title'],
                'episodes': d['episode_count'],
                'last_episode': e['episode'],
                'last_episode_title': e['title'],
            }
        else:
            return { }

    def update(self):
        self._data = _get_detailed(self.id)

        if self._data['poster']:
            self._cover = 'https://cdn.masterani.me/poster/3/{}'.format(self._data['poster'])
