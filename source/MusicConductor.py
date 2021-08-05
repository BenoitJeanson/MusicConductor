from yattag import Doc, indent
import re


class Tone:
    def __init__(self, key) -> None:
        self.set_tone(key)

    def get_tone(self) -> str:
        return self.key

    def set_tone(self, key):
        self.key = key

        self.key_map_bemol = ["A", "Bb", "B", "C", "Db",
                         "D", "Eb", "E", "F", "Gb", "G", "Ab"]
        self.key_map_sharp = ["A", "A#", "B", "C", "C#",
                          "D", "D#", "E", "F", "F#", "G", "G#"]
        self.key_map = self.key_map_bemol if key in [
            "Bb", "C", "Db", "Eb", "F", "Gb", "Ab"] else self.key_map_sharp

        self.key_deg = self.key_map.index(key)

    def get_key_deg(self) -> int:
        return self.key_deg

    def deg_to_note(self, deg) -> str:
        return self.key_map[(deg + self.get_key_deg()) % 12]

    def note_to_deg(self, note) -> int:
        deg = self.key_map_bemol.index(note) if note in self.key_map_bemol else self.key_map_sharp.index(note)
        return (deg - self.get_key_deg()) % 12

    def is_note(self, str):
        return str in self.key_map_bemol or str in self.key_map_sharp


class Note():
    def __init__(self, tone, deg) -> None:
        super().__init__()
        self.tone = tone
        self.deg = deg

    def get_deg(self) -> int:
        return self.deg

    def get_key(self) -> str:
        return self.tone.deg_to_note(self.deg)

    def __str__(self) -> str:
        return str(self.get_key())


class MusicElement:
    def __init__(self) -> None:
        pass

    def get_content(self):
        return str(self)


class EmptyMusicElement(MusicElement):
    def __init__(self) -> None:
        super().__init__()


class StrMusicElement(MusicElement):
    def __init__(self, content) -> None:
        super().__init__()
        self.content = content

    def __str__(self) -> str:
        return self.content


class Chord(MusicElement):
    def __init__(self, note, chord_type="", bass_note=None) -> None:
        super().__init__()
        self.note = note
        self.chord_type = chord_type
        self.bass_note = bass_note

    def has_bass(self):
        return self.bass_note != None

    def __str__(self) -> str:
        chord = str(self.note) + self.chord_type
        if self.has_bass():
            return chord + "/" + str(self.bass_note)
        return chord


class MusicItem:
    def __init__(self,  duration, music_element, resolution) -> None:
        self.music_element = music_element
        self.duration = duration
        self.resolution = 4

    def get_duration(self) -> int:
        return self.duration

    def __str__(self) -> str:
        return str(self.music_element.get_content())


class MusicItemFactory:
    def __init__(self, tone, resolution=4) -> None:
        self.tone = tone
        self.duration = resolution
        self.content = ""
        self.resolution = resolution

    def parse_duration(self, str) -> str:
        dur = str[:1]
        self.duration = self.resolution
        if (dur in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]):
            self.duration = int(dur)
            return str[1:]
        return str

    def identify_note(self, str):
        if (len(str) == 1):
            note_size = 1
        elif(str[1] in ["#", "b"]):
            note_size = 2
        else:
            note_size = 1
        if not self.tone.is_note(str[:note_size]):
            return None, str
        deg = self.tone.note_to_deg(str[:note_size])
        return deg, str[note_size:]

    def parse(self, str) -> MusicItem:
        content = self.parse_duration(str)

        dash = content.find("/")
        if dash != -1:
            n1, n2 = content.split("/")
            deg, chord_type = self.identify_note(n1)
            deg_bass, unused = self.identify_note(n2)
            if deg == None or deg_bass == None:
                return MusicItem(self.duration, StrMusicElement(content), self.resolution)
            else:
                return MusicItem(self.duration, Chord(Note(self.tone, deg), chord_type, Note(self.tone, deg_bass)), self.resolution)
        deg, chord_type = self.identify_note(content)
        if deg == None:
            return MusicItem(self.duration, StrMusicElement(content), self.resolution)
        else:
            return MusicItem(self.duration, Chord(Note(self.tone, deg), chord_type), self.resolution)


class Bar:
    def __init__(self, music_items, bar_resolution) -> None:
        self.music_items = music_items
        self.bar_resolution = bar_resolution

    def __str__(self) -> str:
        return " ".join([str(mi) for mi in self.music_items])

    def to_html(self, doc=None, tag=None, text=None):
        if doc == None:
            doc, tag, text = Doc().tagtext()
        i = 0
        if not self.music_items:
            for j in range(self.bar_resolution):
                with tag('td', klass=('FirstBarItem ' if j == 0 else '') + 'EmptyBar'):
                    continue
        else:
            for mi in self.music_items:
                for j in range(mi.get_duration()):
                    with tag('td', klass=('FirstBarItem ' if i == 0 else '') + 'BarItem'):
                        i += 1
                        if j == 0:
                            text(str(mi))

        return indent(doc.getvalue())


class BarFactory:
    def __init__(self, music_item_factory, resolution=4) -> None:
        self.music_item_factory = music_item_factory
        self.resolution = resolution

    def parse(self, music_items_str) -> Bar:
        music_items = music_items_str.split(" ")
        return Bar([] if music_items[0] == '' else [self.music_item_factory.parse(st) for st in music_items],
                   self.resolution)


class LineBar:
    def __init__(self, bars, comment="", repeat=1) -> None:
        self.bars = bars
        self.comment = comment
        self.repeat = repeat

    def __str__(self) -> str:
        return self.comment + ' ' +\
            str([str(bar) for bar in self.bars]) +\
            ' x' + str(self.repeat)

    def to_html(self, doc=None, tag=None, text=None):
        if doc == None:
            doc, tag, text = Doc().tagtext()
        with tag('td', klass='lineBarComment'):
            text(self.comment)
        for bar in self.bars:
            bar.to_html(doc, tag, text)
        with tag('td', klass='lineBarRepeat'):
            if self.repeat != 1:
                text('x' + str(self.repeat))
        return indent(doc.getvalue())


class LineBarFactory:
    def __init__(self, bar_factory) -> None:
        self.bar_factory = bar_factory

    def parse(self, line_bar_str) -> LineBar:
        comment = ""
        repeat = 1
        bars = []
        for st in line_bar_str.split(','):
            st = st.strip()
            if st[0] == '"':
                comment = st[1:-1]
            elif st[0] == '*':
                repeat = int(st[1:])
            else:
                bars = [self.bar_factory.parse(bar_st)
                        for bar_st in st.split('|')]

        return LineBar(bars, comment, repeat)


class Section:
    def __init__(self, name, repeat, line_bars) -> None:
        self.name = name
        self.line_bars = line_bars
        self.repeat = repeat

    def __str__(self) -> str:
        back = '\n'
        return f"{self.name} {back.join([str(lb) for lb in self.line_bars])} x{self.repeat}"

    def to_html(self, doc=None, tag=None, text=None):
        if doc == None:
            doc, tag, text = Doc().tagtext()

        nb_lines = len(self.line_bars)
        # with tag('table'):
        with tag('tr'):
            with tag('td', ('rowspan', str(max([1, nb_lines]))), klass='sectionName' +
                     (' emptySectionName' if self.name == '' else '')):
                text(self.name)
            if self.line_bars:
                self.line_bars[0].to_html(doc, tag, text)
            if self.repeat != 1:
                with tag('td', ('rowspan', str(max([1, nb_lines]))), klass='sectionRepeat'):
                    text("x" + str(self.repeat))
        if self.line_bars:
            for line in self.line_bars[1:]:
                with tag('tr'):
                    line.to_html(doc, tag, text)

        return indent(doc.getvalue())


class SectionFactory:
    def __init__(self, line_bar_factory) -> None:
        self.line_bar_factory = line_bar_factory

    def parse(self, section_str) -> Section:
        raw_section_content = re.split(r"\n", section_str)
        section_content = []
        for sc in raw_section_content:
            striped = sc.strip()
            if len(striped) != 0:
                section_content.append(striped)
        name = ""
        repeat = 1
        for st in re.split(r",", section_content[0]):
            content = st.strip()
            if len(content) == 0:
                continue
            if content[0] == '"':
                name = content.strip('"')
            elif content[0] == ("*"):
                repeat = int(content[1:])
        return Section(name, repeat, [self.line_bar_factory.parse(st) for st in section_content[1:]])


class Song:
    def __init__(self, title, tone, time, tempo, sections) -> None:
        self.title = title
        self.time = time
        self.tempo = tempo
        self.tone = tone
        self.sections = sections

    def set_key(self, key):
        self.tone.set_tone(key)

    def to_html(self, doc=None, tag=None, text=None):
        if doc == None:
            doc, tag, text = Doc().tagtext()

        doc.asis('<!DOCTYPE html>')
        with tag('html'):
            with tag('head'):
                doc.stag('link', ('rel', "stylesheet"), ('href', 'style.css'))

            with tag('body'):
                with tag('h1'):
                    text(self.title)
                with tag('p', klass="HeaderInfo"):
                    text("Key:")
                    with tag('b'):
                        text(self.tone.get_tone())
                    text("    Time:")
                    with tag('b'):
                        text(self.time)
                    text("    Tempo:")
                    with tag('b'):
                        text(self.tempo)
                    text(" bpm")
                with tag('table'):
                    for section in self.sections:
                        section.to_html(doc, tag, text)
                        with tag('tr', klass='sectionsSeparation'):
                            continue

        return indent(doc.getvalue())


class SongFactory:
    def parse(self, str, section_factory=None, bar_resolution=4):
        sections = str.split('_')
        header = sections[0]
        fields = [st.strip() for st in header.split(',')]
        title = fields[0]
        key = fields[1]
        time = fields[2]
        tempo = fields[3]
        if len(fields) > 4:
            bar_resolution = int(fields[4])
            print(bar_resolution)
        tone = Tone(key)
        if section_factory == None:
            section_factory = SectionFactory(
                LineBarFactory(BarFactory(MusicItemFactory(tone, bar_resolution), bar_resolution)))
        return Song(title, tone, time, tempo, [section_factory.parse(sec) for sec in sections[1:]])


def default_music_item_factory(tone):
    return MusicItemFactory(tone)


def default_bar_factory(tone):
    return BarFactory(default_music_item_factory(tone))


def default_line_bar_factory(tone):
    return LineBarFactory(default_bar_factory(tone))


def default_section_factory(tone):
    return SectionFactory(default_line_bar_factory(tone))
