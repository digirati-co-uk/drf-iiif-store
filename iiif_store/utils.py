import logging

logger = logging.getLogger(__name__)


class ActionBasedSerializerMixin(object):

    serializer_mapping = {
        "default": None,
    }

    def get_serializer_class(self):
        if serializer_class := self.serializer_mapping.get(self.action):
            return serializer_class
        elif serializer_class := self.serializer_mapping.get("default"):
            return serializer_class
        else:
            return self.serializer_class
