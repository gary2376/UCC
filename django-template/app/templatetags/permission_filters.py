from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary and hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None
