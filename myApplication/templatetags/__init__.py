from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Filtre pour accéder à un élément d'un dictionnaire via une clé
    Usage: {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter(name='attr')
def attr(obj, attr_name):
    """
    Filtre pour accéder à un attribut d'un objet
    Usage: {{ obj|attr:"attribute_name" }}
    """
    if obj is None:
        return None
    return getattr(obj, attr_name, None)