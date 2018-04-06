"""
Component that will perform facial recognition via a local machinebox instance.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/image_processing.facebox
"""
import base64
import requests
import logging
import time
import voluptuous as vol

from homeassistant.core import split_entity_id
import homeassistant.helpers.config_validation as cv
from homeassistant.components.image_processing import (
    PLATFORM_SCHEMA, CONF_SOURCE, CONF_ENTITY_ID,
    CONF_NAME, CONF_CONFIDENCE, DEFAULT_CONFIDENCE)
from homeassistant.components.image_processing.microsoft_face_identify import (
    ImageProcessingFaceEntity)

_LOGGER = logging.getLogger(__name__)

CONF_ENDPOINT = 'endpoint'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ENDPOINT): cv.string,
    vol.Optional(CONF_CONFIDENCE, default=DEFAULT_CONFIDENCE):
        vol.All(vol.Coerce(float), vol.Range(min=0, max=100))
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the classifier."""
    entities = []
    for camera in config[CONF_SOURCE]:
        entities.append(Facebox(
            camera.get(CONF_NAME),
            config[CONF_ENDPOINT],
            camera[CONF_ENTITY_ID],
            config[CONF_CONFIDENCE]
        ))
    add_devices(entities)


class Facebox(ImageProcessingFaceEntity):
    """Perform a classification via a Facebox."""

    def __init__(self, name, endpoint, camera_entity, confidence):
        """Init with the API key and model id"""
        super().__init__()
        if name:  # Since name is optional.
            self._name = name
        else:
            self._name = "Facebox {0}".format(
                split_entity_id(camera_entity)[1])
        self._camera = camera_entity
        self._confidence = confidence
        self._url = "http://{}/facebox/check".format(endpoint)
        self._response_time = None

    def process_image(self, image):
        """Process an image."""
        timer_start = time.perf_counter()
        response = requests.post(
            self._url,
            json=self.encode_image(image)
            ).json()

        if response['success']:
            elapsed_time = time.perf_counter() - timer_start
            self._response_time = round(elapsed_time, 1)
            self.total_faces = response['facesCount']  # An int.
            self.faces = response['faces']
            self.process_faces(self.faces, self.total_faces)
        else:
            self.total_faces = "Request_failed"
            self.faces = []

    def encode_image(self, image):
        """base64 encode an image stream."""
        base64_img = base64.b64encode(image).decode('ascii')
        return {"base64": base64_img}

    @property
    def camera_entity(self):
        """Return camera entity id from process pictures."""
        return self._camera

    @property
    def confidence(self):
        """Return minimum confidence for send events."""
        return self._confidence

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return other details about the sensor state."""
        attr = self.state_attributes
        attr.update({'response_time': self._response_time})
        return attr
