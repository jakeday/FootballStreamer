import urllib, urllib2, json, re, webbrowser
from Tkinter import *
import tkMessageBox
from HTMLParser import HTMLParser

def fetch_url(url):
    hdr = { 'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.81 Safari/537.36' }
    request = urllib2.Request(url, headers=hdr)
    return urllib2.urlopen(request)

def fetch_json(url):
    return json.load(fetch_url(url))

def get_games(game_type):
    if game_type == 'NCAA':
        games_json = fetch_json('https://www.reddit.com/r/cfbstreams/new.json?sort=top')
    else:
        games_json = fetch_json('https://www.reddit.com/r/nflstreams/new.json?sort=top')
    games = games_json['data']['children']

    return parse_games(games)

def parse_games(games):
    games_available = []

    for game in games:
        game_title = game['data']['title']
        game_url = game['data']['url'][:-1] + '.json?sort=top'

        if 'Game Thread' in game_title:
            game_data = {}
            game_data['title'] = game_title.replace('Game Thread: ', '')
            game_data['url'] = game_url

            games_available.append(game_data)

    return games_available

def get_streams(self, event, game_url):
    posts = fetch_json(game_url)
    streams = []
    streams_tmp = []
    found_strem = False

    for post in posts:
        if 'children' in post['data']:
            comments = post['data']['children']

            for comment in comments:
                if 'body' in comment['data']:
                    comment_body = comment['data']['body']

                    if self.verified_streams == 0 or 'VERIFIED STREAMERS' in comment_body or comment['data']['author_flair_css_class'] == 'verified':
                        streams_tmp += re.findall("(?P<url>https?://[^\s'\"\)]+)", comment_body)

    for stream_tmp in streams_tmp:
        if not stream_tmp in streams:
            streams.append(stream_tmp)

    if len(streams) > 0:
        found_stream = True

    if found_stream:
        if self.open_all.get() == 1:
            max_streams = len(streams)
        else:
            max_streams = 1

        for idx, stream in enumerate(streams[0:max_streams], start=0):
            if (self.parse_stream.get() == 1):
                html = fetch_url(stream).read()
                parser = ParseStream()
                parser.feed(html)
            else:
                webbrowser.open(stream)
    else:
        tkMessageBox.showinfo("No Stream", "A verified stream could not be found for this game.")

def search_games(self, search, game_type):
    criteria = urllib.quote_plus(search.get())

    if (criteria == ''):
        return get_games(game_type)

    if game_type == 'NCAA':
        games_json = fetch_json('https://www.reddit.com/r/cfbstreams/search.json?q=' + criteria + '&restrict_sr=1')
    else:
        games_json = fetch_json('https://www.reddit.com/r/nflstreams/search.json?q=game%20thread%20' + criteria + '&restrict_sr=1')
    games = games_json['data']['children']

    return self.load_games(parse_games(games))

class ParseStream(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.has_iframe = False
        self.has_src = False
        self.has_allowfullscreen = False
        self.lasttag = None
        self.video_url = ''
        self.stream_url = ''
        self.found_stream = False

    def handle_starttag(self, tag, attrs):
        self.video_url = ''
        self.found_stream = False
        if tag == 'iframe':
            self.has_iframe = True
            for name, value in attrs:
                if name.lower() == 'allowfullscreen':
                    self.has_allowfullscreen = True
                    self.lasttag = tag
                if name == 'src':
                    self.video_url = value
                    self.has_src = True
            if self.has_iframe and self.has_allowfullscreen and self.has_src:
                self.found_stream = True
                self.stream_url = self.video_url

    def handle_endtag(self, tag):
        if tag == 'iframe':
            self.has_iframe = False
            self.has_allowfullscreen = False
            self.has_src = False
            self.video_url = ''

    def handle_data(self, data):
        if self.found_stream and self.stream_url != '':
            webbrowser.open(self.stream_url)
            self.stream_url = ''
            self.found_stream = False

class FootballStreamer(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()

        self.header_frame = Frame(self.master)
        self.header_frame.pack(side=TOP, fill=BOTH, expand=TRUE)

        self.settings_frame = Frame(self.master)
        self.settings_frame.pack(side=TOP, fill=BOTH, expand=TRUE)

        self.search_frame = Frame(self.master)
        self.search_frame.pack(side=TOP, fill=BOTH, expand=TRUE)

        self.bottom_frame = Frame(self.master)
        self.bottom_frame.pack(side=BOTTOM, fill=BOTH, expand=TRUE)

        self.canvas = Canvas(self.bottom_frame)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)

        self.scrollbar = Scrollbar(self.bottom_frame, orient=VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y, expand=FALSE)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.games_frame = Frame(self.canvas)
        self.games_frame.pack(side=BOTTOM, fill=BOTH, expand=TRUE)

        self.canvas.create_window((0,0), window=self.games_frame,anchor='nw')
        self.games_frame.bind("<Configure>", self.aux_scroll_function)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind_all("<Button-4>", self.on_mousewheel)
        self.canvas.bind_all("<Button-5>", self.on_mousewheel)

        master.geometry('390x520')
        master.title('Football Streamer')

        self.lb_title = Label(self.header_frame, text='Football Streamer')
        self.lb_title.config(font=("Verdana", 22))
        self.lb_title.pack(side=TOP)

        self.gtvar = StringVar(root)

        self.game_types = {'NFL','NCAA'}
        self.gtvar.set('NFL')

        self.gametype_menu = OptionMenu(self.header_frame, self.gtvar, *self.game_types)
        self.gametype_menu.pack(side=TOP, fill=X, expand=TRUE)
        self.gtvar.trace('w', self.change_game_type)

        self.verified_streams = IntVar(value=1)
        self.verified_button = Checkbutton(self.settings_frame, text="Verified Only", variable=self.verified_streams)
        self.verified_button.pack(side=LEFT, fill=X, expand=TRUE)

        self.open_all = IntVar(value=0)
        self.open_all_button = Checkbutton(self.settings_frame, text="Open All", variable=self.open_all)
        self.open_all_button.pack(side=RIGHT, fill=X, expand=TRUE)

        self.parse_stream = IntVar(value=1)
        self.parse_button = Checkbutton(self.settings_frame, text="Stream Only", variable=self.parse_stream)
        self.parse_button.pack(side=RIGHT, fill=X, expand=TRUE)

        self.search_string = StringVar()
        self.search_entry = Entry(self.search_frame, textvariable=self.search_string, bg='#ffffff')
        self.search_entry.pack(side=LEFT, fill=X, expand=TRUE)

        self.search_button = Button(self.search_frame, text="Search", command=lambda game_type=self.gtvar.get(): search_games(self, self.search_entry, game_type))
        self.search_button.pack(side=RIGHT)

        self.color_schemes = [{'bg': '#ADD8E6', 'fg': '#000000'}, {'bg': '#00BFFF', 'fg': '#000000'}]

        self.load_games(get_games('NFL'))

    def load_games(self, games):
        for self.label in self.games_frame.children.values():
            self.label.destroy()

        if len(games) > 0:
            self.idx = 0
            for self.game in games:
                self.idx += 1
                self.game_label = Label(self.games_frame, text=self.game['title'], bg='#00BFFF', fg='#000000', pady=10, cursor='hand1')
                self.game_label.pack(side=TOP, padx=0, pady=0, fill=X, expand=TRUE)
                self.game_label.bind('<Button-1>', lambda event, url=self.game['url']: get_streams(self, event, url))
                self.set_game_color(self.idx, self.game_label)
        else:
            self.game_label = Label(self.games_frame, text='There are currently no active streams for this selection.', bg='lightgrey', fg='black', pady=10)
            self.game_label.pack(side=TOP, padx=0, pady=0, fill=X, expand=TRUE)

    def change_game_type(self, *args):
        games = get_games(self.gtvar.get())
        self.load_games(games)

    def set_game_color(self, position, game):
        _, scheme_choice = divmod(position, 2)

        game_scheme = self.color_schemes[scheme_choice]

        game.configure(bg=game_scheme['bg'])
        game.configure(fg=game_scheme['fg'])

    def aux_scroll_function(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'), width=340, height=420)

    def on_mousewheel(self, event):
        global count
        count = 0

        def delta(event):
            if event.num == 5 or event.delta < 0:
                return -1
            return 1

        count += delta(event)
        self.canvas.yview_scroll(count, 'units')

root = Tk()
iconimg = PhotoImage(file=r'icon.png')
root.tk.call('wm', 'iconphoto', root._w, iconimg)
footballstreamer = FootballStreamer(master=root)
footballstreamer.mainloop()
