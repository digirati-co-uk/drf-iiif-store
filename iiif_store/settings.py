import logging
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
        "CANONICAL_HOSTNAME": "", 
        "INDEX_IIIF_RESOURCES": True, # If True, IIIFResources will be indexed into the search_service on save. 
        "ASYNC_INDEXING": False, # If True, indexing will be carried out asynchronously in a django q task. 
        }


class AppSettings(object):
    def __init__(self, settings_key=None, default_settings={}):
        self.settings_key = settings_key
        self.default_settings = default_settings

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, self.settings_key, {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.default_settings:
            raise AttributeError(f"Invalid setting {attr} for {self.settings_key}")

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.default_settings[attr]
        # Cache the result
        setattr(self, attr, val)
        return val



iiif_store_settings = AppSettings("IIIF_STORE", DEFAULT_SETTINGS)
