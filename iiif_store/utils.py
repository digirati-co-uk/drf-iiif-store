import pydoc
import logging

from rest_framework.relations import HyperlinkedRelatedField

logger = logging.getLogger(__name__)

def run_task(task, **kwargs): 
    if not callable(task):
        task_class = pydoc.locate(task)
    else: 
        task_class = task
   
    logger.debug(f'Running task: ({task_class}, {kwargs})')
    task = task_class(**kwargs)
    result = task.run()
    return result


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


class HyperlinkedMultiArgRelatedField(HyperlinkedRelatedField):
    def __init__(self, view_name=None, **kwargs):
        kwargs["read_only"] = True
        self.url_kwarg_mapping = kwargs.pop("url_kwarg_mapping", {})
        self.url_kwarg_field_mapping = kwargs.pop("url_kwarg_field_mapping", {})
        super().__init__(view_name, **kwargs)

    def use_pk_only_optimization(self):
        return False

    def get_url(self, obj, view_name, request, format):
        if hasattr(obj, "pk") and obj.pk in (None, ""):
            return None
        kwargs = {**self.url_kwarg_mapping}
        for url_kwarg, obj_field in self.url_kwarg_field_mapping.items():
            obj_attr = obj
            for obj_field in obj_field.split("."):
                # n.b. default obj_field for getattr. Will use this as the url value if the attribute isn't present. 
                obj_attr = getattr(obj_attr, obj_field, obj_field)
            kwargs[url_kwarg] = obj_attr
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)

