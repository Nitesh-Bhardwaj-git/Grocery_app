from django import template

register = template.Library()

def pluralize_unit(unit, value):
    value = float(value)
    if unit in ['kg', 'litre', 'pack', 'dozen']:
        return unit  # No plural
    if unit == 'g':
        return 'gram' if value == 1 else 'grams'
    if unit == 'ml':
        return 'millilitre' if value == 1 else 'millilitres'
    if unit == 'pcs':
        return 'piece' if value == 1 else 'pieces'
    return unit

@register.filter
def unit_display(item):
    value = item.unit_value
    unit = item.unit
    # Remove .0 for whole numbers
    if value == int(value):
        value = int(value)
    return f"{value} {pluralize_unit(unit, value)}" 