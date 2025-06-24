from collections.abc import MutableMapping

from rest_framework import mixins
from rest_framework.renderers import JSONRenderer
from rest_framework.viewsets import GenericViewSet


def flatten(dictionary, parent_key='', separator='_'):
    items = []
    if isinstance(dictionary, dict):
        for key, value in dictionary.items():
            new_key = parent_key + separator + key if parent_key else key
            if isinstance(value, MutableMapping):
                items.extend(flatten(value, new_key, separator=separator).items())
            else:
                items.append((new_key, value))
        return dict(items)
    return dictionary


class FlatternJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        data = flatten(data)
        return super(FlatternJSONRenderer, self).render(data, accepted_media_type, renderer_context)


class CustomModelViewSet(mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.ListModelMixin,
                         GenericViewSet):
    renderer_classes = [FlatternJSONRenderer]
