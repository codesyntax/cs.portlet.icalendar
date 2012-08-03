from Products.CMFPlone.utils import safe_unicode
from zope.interface import implements

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from zope import schema
from zope.formlib import form

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from cs.portlet.icalendar import icalendarMessageFactory as _
from plone.memoize.ram import cache

import urllib2
from icalendar import Calendar
from Products.ATContentTypes.utils import dt2DT

class IICalendarPortlet(IPortletDataProvider):
    """A portlet
It inherits from IPortletDataProvider because for this portlet, the
data that is being rendered and the portlet assignment itself are the
same.
"""

    portlet_title = schema.TextLine(title=_(u"Title"),
                            description=_(u"Enter the title of the portlet"),
                            required=True)

    url = schema.TextLine(title=_(u"URL"),
                          description=_(u"Enter the URL of the ICS file with the event data"),
                          required=True,
                          )

    limit = schema.Int(title=_(u'Number of items to show in the portlet.'),
                       description=_(u'If you enter 0, all items will be shown'),
                       default=0,
                       required=True
                       )

    show_start = schema.Bool(title=_(u'Show the start date of the event?'),
                            required=False,
                            default=True,
                           )

    show_end = schema.Bool(title=_(u'Show the end date of the event?'),
                           required=False,
                           default=True,
                           )

    cache_time = schema.Int(title=_(u'Cache of the ICS data in seconds'),
                            required=True,
                            default=3600,
                            )


class Assignment(base.Assignment):
    """Portlet assignment.

This is what is actually managed through the portlets UI and associated
with columns.
"""

    implements(IICalendarPortlet)

    def __init__(self, 
                 portlet_title=u"", 
                 url=u'',
                 limit=0,
                 show_start=True,
                 show_end=True,
                 cache_time=3600):


        self.portlet_title = portlet_title
        self.url = url
        self.limit = limit
        self.show_start = show_start
        self.show_end = show_end
        self.cache_time = cache_time


    def title(self):
        return self.portlet_title

class Renderer(base.Renderer):
    """Portlet renderer.

This is registered in configure.zcml. The referenced page template is
rendered, and the implicit variable 'view' will refer to an instance
of this class. Other methods can be added and referenced in the template.
"""

    render = ViewPageTemplateFile('calendarportlet.pt')

    def title(self):
        return self.data.portlet_title

    def _render_cache_key(func, item):
        return item.data.cache_time

    @cache(_render_cache_key)
    def get_items(self):
        try:
            sock = urllib2.urlopen(self.data.url)
        except:
            return []
        cal = Calendar.from_ical(sock.read())
        res = []
        for item in cal.walk():
            if item.name == 'VEVENT':
                d = {}
                d['text'] = safe_unicode(item.get('SUMMARY', ''))
                start = item.get('DTSTART', None)
                d['start'] = start and dt2DT(start.dt) or ''
                end = item.get('DEND', None)
                d['end'] = end and dt2DT(end.dt) or ''
                d['location'] = safe_unicode(item.get('LOCATION', ''))
                d['subject'] = safe_unicode(item.get('CATEGORIES', ''))
                res.append(d)

        if not self.data.limit:
            return res
        else:
            return res[:self.data.limit]

class AddForm(base.AddForm):
    """Portlet add form.

This is registered in configure.zcml. The form_fields variable tells
zope.formlib which fields to display. The create() method actually
constructs the assignment that is being added.
"""
    form_fields = form.Fields(IICalendarPortlet)

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form.

This is registered with configure.zcml. The form_fields variable tells
zope.formlib which fields to display.
"""
    form_fields = form.Fields(IICalendarPortlet)