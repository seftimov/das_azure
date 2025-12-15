from django import template

register = template.Library()


@register.filter
def get_item(d, key):
    return d.get(key, "")


@register.filter
def add_class(field, css):
    """
    Usage: {{ form.field|add_class:"form-control" }}
    """
    return field.as_widget(attrs={"class": css})
