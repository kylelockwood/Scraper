#! python3

import sys
import urllib
import requests
import json
from bs4 import BeautifulSoup
import html
import datetime as dt

HELP = ('Usage: scrape.py <link> -<command> <term>\n'
        'Eschewing commands will print entire soup.\n'
        '   COMMANDS\n'
        '     -tags             : Retruns all tag names\n'
        '     -tag  <tag name>  : Returns all elements containing attribute\n'
        '     -find <string>    : Retruns results containing \n'
        '     -max <int | none> : Set the maximum number of characters to display from -find (default 100)\n'
        '     -save <filename>  : Saves data to a .txt file. Default filename is SCRAPE_<slug>_<timestamp>.txt')

class Scrape:
    def __init__(self):
        self.commands = self.validate_inputs()
        self.data = []
        char_max = 100
        if self.commands:
            if '-max' in self.commands:
                if str(self.commands['-max']).lower() == 'none':
                    char_max = -1
                else:
                    try:
                        char_max = int(self.commands['-max'])
                    except ValueError:
                        sys.exit('Error: -max characters must be an integer.')

            if '-tags' in self.commands:
                tags = [tag.name for tag in self.get_soup().find_all()]
                tags = list(dict.fromkeys(tags))
                print('Tags :\n')
                for tag in tags:
                    print(tag)
                sys.exit()

            elif '-tag' in self.commands:
                tag_list = []
                find_list = []
                soup = self.get_soup()
                for itm in soup.find_all(self.commands['-tag']):
                    tag_list.append(str(itm))
                
                if '-find' in self.commands:
                    search = self.commands['-find']
                    for itm in tag_list:
                        if search in itm:
                            find_list.append(itm)
                    if not find_list:
                        sys.exit(f'No results for search \'{search}\'.')
                if find_list:
                    self.data = find_list
                else:
                    self.data = tag_list

            elif '-find' in self.commands and not '-tag' in self.commands:
                soup = self.get_soup()
                print('Parsing...')
                tags = [tag.name for tag in soup.find_all()]
                tags = list(dict.fromkeys(tags))
                elipsis = '...'
                if char_max == -1:
                    elipsis = ''
                for tag in tags:
                    for itm in soup.find_all(tag):
                        if self.commands['-find'] in str(itm):
                            self.data.append(str(itm)[:char_max] + elipsis)

            if '-save' in self.commands:
                if not self.data:
                    self.data = self.get_soup() # temp
                self.save_meta(self.data)
                sys.exit(' Complete.')

        else:
            self.data = self.get_soup().find_all()

        if self.data:
            for thng in self.data:
                print(thng)
            #print()
            sys.exit(f'\nReturned {len(self.data)} result(s).')
        else:
            sys.exit('No results returned.')

    def validate_inputs(self):
        try:
            args = sys.argv
            self.link = args[1]
            if not self.link.startswith('http'):
                raise IndexError
        except IndexError:
            sys.exit(f'Missing valid url: {HELP}')

        commands = {}
        for index, arg in enumerate(args):
            if arg.startswith('-'):
                if arg == '-tags':
                    commands[arg] = None
                    continue
                try:
                    term = args[index + 1]
                    if term.startswith('-'):
                        raise IndexError
                    commands[arg] = term
                except IndexError:
                    if arg == '-save':
                        commands[arg] = None
                        continue
                    sys.exit(f'Error: Command \'{arg}\' missing <term>')
        if not commands:
            #sys.exit('No commands passed.')
            return None
        return commands

    def get_soup(self):
        print('Fetching metadata...')
        page = urllib.request.urlopen(self.link)
        soup = BeautifulSoup(page.read(), "html.parser")
        return soup

    def save_meta(self, data):
        outfile = self.commands['-save']
        if not outfile:
            link = self.link.split('/')[-1]
            stamp = dt.datetime.now().strftime('%m%d%Y_%H%M%S')
            outfile = 'SCRAPE_' + link + '_'+ stamp + '.txt' 
        if not outfile.endswith('.txt'):
            outfile = outfile + '.txt'
        
        print(f'Saving to file \'{outfile}\'...', flush=True, end='')
        data = '\r'.join(data)
        with open(outfile, 'w') as f:
            try:
                f.write(str(data))
            except UnicodeEncodeError:
                data = html.unescape(data)
                f.write(str(data))


def get_yt_meta(link):
    lookup = {'meta' : 'content', 'link' : 'href'}
    properties = {'itemprop' : ['name', 'datePublished', 'videoId', 'thumbnailUrl', 'embedUrl']}
    meta = get_meta(link, lookup, properties)
    return {'name' : meta['name'],
            'published': meta['datePublished'], 
            'id': meta['videoId'],
            'thumb' : meta['thumbnailUrl'],
            'embed' : meta['embedUrl']
            }

def get_fb_meta(link):
    #'img', {'src':re.compile('.jpg')})
    lookup = {'meta' : 'content', 'link' : 'href'}
    properties = {'property' : ['og:title', 'og:image'], 'rel' : [['canonical']]}  
    meta = get_meta(link, lookup, properties)
    name = meta['og:title']
    thumb = html.unescape(meta['og:image'])
    url = meta['[\'canonical\']']
    vidid = url.split('/')[-2]
    page = url.split('/')[3]
    embed = 'https://www.facebook.com/plugins/video.php?href=https%3A%2F%2Fwww.facebook.com%2F' + page + '%2Fvideos%2F' + vidid + '&amp'
    return {'name' : name,
            'published' : '',
            'id' : vidid,
            'thumb' : thumb,
            'embed' : embed
            }

def find_meta(lookup, properties):
    meta_dict = {}
    for attr in lookup:
        #print(f'{attr=}')
        for itm in soup.find_all(attr):
            #print(f'{itm=}') # meta, link
            for prop in properties:  
                #print(f'{prop=}') # property
                for p in properties[prop]: # og:title, canonical
                    #print(f'{p=}')
                    ip = itm.get(prop) # property
                    #print(type(ip))
                    content = itm.get(lookup[attr]) # content, href
                    #print(f'{ip=}')
                    if content and ip == p: 
                        #print(f'{p=}')
                        #print(f'{content=}')
                        #if content:
                        meta_dict[str(p)] = content
    return meta_dict

def load_json(filename):
    try:
        with open(filename) as f:
            data = json.load(f)
    except Exception as e:
        sys.exit(f'  Unable to load JSON data. {e}')
    return data

if __name__ == '__main__':

    meta = Scrape()
    #meta.save_meta(meta.soup, 'testt.txt')
