from kivy.uix.boxlayout import BoxLayout
from kivy.adapters.dictadapter import DictAdapter
from kivy.adapters.listadapter import ListAdapter
from kivy.properties import ObjectProperty, ListProperty, AliasProperty
from kivy.uix.listview import (ListItemButton, ListItemLabel, CompositeListItem,
                               ListView)
from kivy.lang import Builder


class GridView(BoxLayout):
    """Workaround solution for grid view by using 2 list view.
    Sometimes the height of lines is shown properly."""

    def _get_hd_adpt(self):
        return self.ids.header_view.adapter

    header_adapter = AliasProperty(_get_hd_adpt, None)
    '''
    '''

    def _get_cnt_adpt(self):
        return self.ids.content_view.adapter

    content_adapter = AliasProperty(_get_cnt_adpt, None)
    '''
    '''

    headers = ListProperty([])
    '''
    '''

    widths = ListProperty([])
    '''
    '''

    data = ListProperty([])
    '''
    '''

    getter = ObjectProperty(lambda item, i: item[i])
    '''
    '''
    on_context_menu = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(GridView, self).__init__(**kwargs)
        self.on_headers(self, self.headers)

    def on_widths(self, instance, value):
        self.on_headers(instance, self.headers)

    def on_headers(self, instance, value):
        if not (value and self.canvas and self.headers):
            return
        widths = self.widths
        if len(self.widths) != len(value):
            return
        if widths is not None:
            widths = ['%sdp' % i for i in widths]

        def generic_args_converter(row_index,
                                   item,
                                   is_header=True,
                                   getter=self.getter):
            cls_dicts = []

            for i, header in enumerate(self.headers):
                kwargs = {
                    'halign': 'left',
                    'size_hint_y': None,
                    'height': '30dp',
                    'text': self.getter(item, i),
                }

                if is_header:
                    kwargs['background_color'] = kwargs['selected_color'] = [0, 1, 1, 1]
                else:  # this is content
                    if self.on_context_menu is not None:
                        kwargs['on_press'] = self.on_context_menu

                if widths is not None:  # set width manually
                    kwargs['size_hint_x'] = None
                    kwargs['width'] = widths[i]

                cls_dicts.append({
                    'cls': ListItemButton,
                    'kwargs': kwargs,
                })

            return {
                'id': item[-1],
                'size_hint_y': None,
                'height': '30dp',
                'cls_dicts': cls_dicts,
            }

        def header_args_converter(row_index, item):
            return generic_args_converter(row_index, item)

        def content_args_converter(row_index, item):
            return generic_args_converter(row_index, item, is_header=False)


        self.ids.header_view.adapter = ListAdapter(data=[self.headers],
                                   args_converter=header_args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=CompositeListItem)

        self.ids.content_view.adapter = ListAdapter(data=self.data,
                                   args_converter=content_args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=CompositeListItem)
        self.content_adapter.bind_triggers_to_view(self.ids.content_view._trigger_reset_populate)
