import string

from django import template
from django.conf import settings
from classytags.arguments import Argument, MultiValueArgument
from classytags.core import Tag, Options
from django.template.defaultfilters import safe

from django.core.cache import cache
from ..models import Placeholder

from cms.templatetags.cms_tags import PlaceholderOptions
from django.utils.safestring import mark_safe

register = template.Library()


class RenderPlaceholder(Tag):
    name = 'appcms_placeholder'
    options = Options(
        Argument('name'),
        Argument('width', default=None, required=False),
    )

    def render_tag(self, context, name, width):

        def _get_placeholder(name, context, width):
            placeholder, created = Placeholder.objects.get_or_create(name=name)
            placeholder.placeholder.slot = name
            return safe(placeholder.placeholder.render(context, width))

        request = context.get('request', None)
        if not request:
            return ''
        if not name:
            return ''

        if not request.user.is_staff:
            language_code = request.LANGUAGE_CODE
            cache_key = filter(string.printable.__contains__, 'placeholder-%s-%s' % (name, language_code))
            cached = cache.get(cache_key)
            if cached:
                return cached
            else:
                resp = _get_placeholder(name, context, width)
                cache.set(cache_key, resp, 60)
                return resp

        return _get_placeholder(name, context, width)
register.tag(RenderPlaceholder)


class RenderGetPlaceholder(Tag):
    """
    Render the content of a placeholder to a variable. Can be provided
    with the name of the placholder (i.e. "Header" in the case of a normal
    CMS page) or a template variable containing a placeholder (i.e. myentry.content in the
    case of an external app using a placeholder)

    {% get_placeholder ["string"|placeholder_var] as variable_name %}

    e.g.
    {% load extra_cms_tags %}
    {% get_placeholder "My Placeholder" as my_placeholder %}

    {% if my_placeholder %}
    <div>
        {{ my_placeholder }}
    </div>
    {% endif %}
    """
    name = "get_placeholder"

    options = PlaceholderOptions(
        Argument('name', resolve=True),
        MultiValueArgument('extra_bits', required=False, resolve=False),
        Argument('width', default=None, required=False),
        'as',
        Argument('varname', resolve=False, required=True),
        blocks=[
            ('endplaceholder', 'nodelist'),
        ],
    )

    def render_tag(self, context, name, extra_bits, width, varname, nodelist=None):
        def _get_placeholder(name, context, width):
            placeholder, created = Placeholder.objects.get_or_create(name=name)
            placeholder.placeholder.slot = name
            return safe(placeholder.placeholder.render(context, width))

        request = context.get('request', None)

        orginal_language_code = request.LANGUAGE_CODE
        default_language_code = settings.LANGUAGE_CODE[:2]

        content = _get_placeholder(name, context, None)
        if not content:
            request.LANGUAGE_CODE = default_language_code
            content = _get_placeholder(name, context, None)
            request.LANGUAGE_CODE = orginal_language_code

        context[varname] = mark_safe(content)
        return ""

    def get_name(self):
        # Fix some template voodoo causing errors
        if isinstance(self.kwargs['name'].var, StringValue):
            return self.kwargs['name'].var.value.strip('"').strip("'")
        return self.kwargs['name'].var.var

register.tag(RenderGetPlaceholder)
