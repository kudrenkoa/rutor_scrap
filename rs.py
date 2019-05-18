#!/usr/bin/env python
from bs4 import BeautifulSoup
from bs4.element import Tag

import urwid
import argparse
import urllib.request
import webbrowser
from multiprocessing.dummy import Pool
from os import cpu_count


class TorrentInfo:
    date = ''
    uri = ''
    size = ''
    name = ''
    sids = ''
    pirs = ''

    def __str__(self):
        return f'{self.date} || {self.name} || {self.size} || {self.sids} || {self.pirs}'


class RutorParser:
    uri_start = 'http://rutor.is/search/0/0/000/2/'
    tr_classes = ['gai', 'tum']

    def get_html_page(self, uri: str):
        fp = urllib.request.urlopen(uri)
        mybytes = fp.read()
        page = mybytes.decode("utf8")
        fp.close()
        return page

    def parse(self, data: str):
        result_uri = self.uri_start + data.replace(' ', '%20')
        html = self.get_html_page(result_uri)
        bs = BeautifulSoup(html, 'html.parser')
        p = Pool(cpu_count())
        res = p.map(self.get_torrent_info_from_tag, bs.findAll(self.find_tag_tr))
        p.close()
        p.join()
        return res

    def find_tag_tr(self, tag: Tag):
        return tag.name == 'tr' and tag.has_attr('class') and tag['class'][0] in self.tr_classes

    def get_torrent_info_from_tag(self, tr: Tag):
        children = tr.findChildren('td', recursive=False)
        child_len = len(children)
        t_info = TorrentInfo()
        t_info.date = children[0].text
        ch_buff = children[1].findChildren('a', recursive=False)
        t_info.uri = ch_buff[1]['href']
        t_info.name = ch_buff[2].text
        t_info.size = children[2 if child_len == 4 else 3].text
        # в зависимости от наличия комментариев
        ch_buff = children[3 if child_len == 4 else 4].findChildren('span', recursive=False)
        t_info.sids = ch_buff[0].text
        t_info.pirs = ch_buff[1].text
        return t_info


def get_data_arg():
    parser = argparse.ArgumentParser(description="Search data from rutor.is")
    parser.add_argument("--search", type=str, help="data for search")
    args = parser.parse_args()
    if args.search is None:
        print('no argument found, exiting...')
        exit(-1)
    return args.search


def menu(title, tor_list):
    body = [urwid.Text(title), urwid.Divider()]

    for torrent_info in tor_list:
        button = urwid.Button(str(torrent_info))
        urwid.connect_signal(button, 'click', item_chosen, torrent_info)
        body.append(urwid.AttrMap(button, None, focus_map='reversed'))
    return urwid.ListBox(urwid.SimpleFocusListWalker(body))


def item_chosen(button, choice: TorrentInfo):
    webbrowser.open_new(choice.uri)


def exit_on_key(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()


if __name__ == '__main__':
    data = get_data_arg()
    rp = RutorParser()
    torrents_list = rp.parse(data)
    main = urwid.Padding(menu(u'Rutor Parser', torrents_list), left=2, right=2)
    top = urwid.Overlay(main, urwid.SolidFill(u'\N{MEDIUM SHADE}'),
                        align='center', width=('relative', 60),
                        valign='middle', height=('relative', 60),
                        min_width=20, min_height=9)
    urwid.MainLoop(top, palette=[('reversed', 'standout', '')], unhandled_input=exit_on_key).run()
