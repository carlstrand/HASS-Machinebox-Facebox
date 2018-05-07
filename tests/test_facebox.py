"""The tests for the facebox component."""
import requests_mock

from homeassistant.const import (CONF_IP_ADDRESS, CONF_PORT)
from homeassistant.setup import setup_component
import homeassistant.components.image_processing as ip

from tests.common import assert_setup_component

MOCK_IP = '192.168.0.1'
MOCK_PORT = '8080'

MOCK_RESPONSE = """
{"facesCount": 1,
"success": True,
"faces":['face_data']}
"""

VALID_ENTITY_ID = 'image_processing.facebox_demo_camera'
VALID_CONFIG = {
    ip.DOMAIN: {
        'platform': 'facebox',
        CONF_IP_ADDRESS: MOCK_IP,
        CONF_PORT: MOCK_PORT,
        ip.CONF_SOURCE: {
            ip.CONF_ENTITY_ID: 'camera.demo_camera'}
        },
    'camera': {
        'platform': 'demo'
        }
    }


def test_setup_platform(hass):
    """Setup platform with one entity."""

    with assert_setup_component(1, ip.DOMAIN):
        setup_component(hass, ip.DOMAIN, VALID_CONFIG)

    assert hass.states.get(VALID_ENTITY_ID)


def test_process_image(hass):
    """Test processing of an image."""

    with assert_setup_component(1, ip.DOMAIN):
        setup_component(hass, ip.DOMAIN, VALID_CONFIG)
    assert hass.states.get(VALID_ENTITY_ID)

    with requests_mock.Mocker() as mock_req:
        url = "http://{}:{}/facebox/check".format(MOCK_IP, MOCK_PORT)
        mock_req.get(url, text=MOCK_RESPONSE)
        ip.scan(hass, entity_id=VALID_ENTITY_ID)
        hass.block_till_done()

    state = hass.states.get(VALID_ENTITY_ID)
    assert state.state == '1'
