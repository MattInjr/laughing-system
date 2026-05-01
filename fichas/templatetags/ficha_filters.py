from django import template

register = template.Library()

@register.filter
def attr_value(ficha, attr):
    return getattr(ficha, attr, '')

@register.filter
def bonus_value(ficha, attr):
    return getattr(ficha, f'bonus_{attr}', '')