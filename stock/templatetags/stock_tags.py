from django import template

register = template.Library()

@register.filter
def get_field(form, pk):
    field_name = f'stock_{pk}'
    return form[field_name]