import pydoc
import logging

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
