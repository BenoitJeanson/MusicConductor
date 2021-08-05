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
        deg = self.key_map_bemol.index(
            note) if note in self.key_map_bemol else self.key_map_sharp.index(note)
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


class Melody:
    def __init__(self, notes, duration) -> None:
        self.notes = notes
        self.duration = duration

    def __str__(self) -> str:
        return '-'.join([str(n) for n in self.notes])


class MusicItem:
    def __init__(self,  duration, music_element, resolution, is_first_in_bar, melody=None) -> None:
        self.music_element = music_element
        self.duration = duration
        self.resolution = 4
        self.is_first_in_bar = is_first_in_bar
        self.melody = melody

    def get_duration(self) -> int:
        return self.duration

    def __str__(self) -> str:
        return str(self.music_element.get_content() + '->' + str(self.melody))

    def to_html(self, doc=None, tag=None, text=None):
        if doc == None:
            doc, tag, text = Doc().tagtext()
        for j in range(self.duration):
            with tag('td', klass=('FirstBarItem ' if self.is_first_in_bar and j == 0 else '') + 'BarItem'):
                if j == 0:
                    text(str(self.music_element.get_content()))


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
        key = re.findall('[A-G][#b]|[A-G]', str)
        if not key or not self.tone.is_note(key[0]):
            return None, str
        deg = self.tone.note_to_deg(key[0])
        return deg, str[len(key[0]):]

    def parse_melody(self, str):
        return(Melody(
            [Note(self.tone, self.tone.note_to_deg(st)) for st in str.split(' ')], self.duration))

    def parse(self, str, is_first_in_bar) -> MusicItem:
        content = self.parse_duration(str)

        melody_str = re.findall('\[.*\]', content)
        melody = self.parse_melody(melody_str[0][1:-1]) if melody_str else None
        element_str = content.split('[')[0]

        dash = element_str.find("/")
        if dash != -1:
            n1, n2 = element_str.split("/")
            deg, chord_type = self.identify_note(n1)
            deg_bass, unused = self.identify_note(n2)
            if deg == None or deg_bass == None:
                return MusicItem(self.duration, StrMusicElement(element_str), self.resolution, is_first_in_bar,melody)
            else:
                return MusicItem(self.duration, Chord(Note(self.tone, deg), chord_type, Note(self.tone, deg_bass)), self.resolution, is_first_in_bar)
        deg, chord_type = self.identify_note(element_str)
        if deg == None:
            return MusicItem(self.duration, StrMusicElement(element_str), self.resolution, is_first_in_bar,melody)
        else:
            return MusicItem(self.duration, Chord(Note(self.tone, deg), chord_type), self.resolution, is_first_in_bar,melody)


class Bar:
    def __init__(self, music_items, bar_resolution) -> None:
        self.music_items = music_items
        self.bar_resolution = bar_resolution

    def __str__(self) -> str:
        return " ".join([str(mi) for mi in self.music_items])

    def to_html(self, doc=None, tag=None, text=None):
        if doc == None:
            doc, tag, text = Doc().tagtext()
        if not self.music_items:
            for j in range(self.bar_resolution):
                with tag('td', klass=('FirstBarItem ' if j == 0 else '') + 'EmptyBar'):
                    continue
        else:
            for mi in self.music_items:
                mi.to_html(doc, tag, text)

        return indent(doc.getvalue())


class BarFactory:
    def __init__(self, music_item_factory, resolution=4) -> None:
        self.music_item_factory = music_item_factory
        self.resolution = resolution

    def parse(self, music_items_str) -> Bar:
        music_items = re.findall('\S*\[[^\[]*\]|\S+', music_items_str)
        return Bar([] if not music_items else [
            self.music_item_factory.parse(st, i == 0) for i, st in enumerate(music_items)], self.resolution)


class BarLine:
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


class BarLineFactory:
    def __init__(self, bar_factory) -> None:
        self.bar_factory = bar_factory

    def parse(self, bar_line_str) -> BarLine:
        comment = ""
        repeat = 1
        bars = []
        for st in bar_line_str.split(';'):
            st = st.strip()
            if st[0] == '"':
                comment = st[1:-1]
            elif st[0] == '*':
                repeat = int(st[1:])
            else:
                bars = [self.bar_factory.parse(bar_st)
                        for bar_st in st.split('|')]

        return BarLine(bars, comment, repeat)


class Section:
    def __init__(self, name, repeat, bar_lines) -> None:
        self.name = name
        self.bar_lines = bar_lines
        self.repeat = repeat

    def __str__(self) -> str:
        back = '\n'
        return f"{self.name} {back.join([str(lb) for lb in self.bar_lines])} x{self.repeat}"

    def to_html(self, doc=None, tag=None, text=None):
        if doc == None:
            doc, tag, text = Doc().tagtext()

        nb_lines = len(self.bar_lines)
        # with tag('table'):
        with tag('tr'):
            with tag('td', ('rowspan', str(max([1, nb_lines]))), klass='sectionName' +
                     (' emptySectionName' if self.name == '' else '')):
                text(self.name)
            if self.bar_lines:
                self.bar_lines[0].to_html(doc, tag, text)
            if self.repeat != 1:
                with tag('td', ('rowspan', str(max([1, nb_lines]))), klass='sectionRepeat'):
                    text("x" + str(self.repeat))
        if self.bar_lines:
            for line in self.bar_lines[1:]:
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
        for st in re.split(r";", section_content[0]):
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
        fields = [st.strip() for st in header.split(';')]
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
                BarLineFactory(BarFactory(MusicItemFactory(tone, bar_resolution), bar_resolution)))
        return Song(title, tone, time, tempo, [section_factory.parse(sec) for sec in sections[1:]])


def default_music_item_factory(tone):
    return MusicItemFactory(tone)


def default_bar_factory(tone):
    return BarFactory(default_music_item_factory(tone))


def default_bar_line_factory(tone):
    return BarLineFactory(default_bar_factory(tone))


def default_section_factory(tone):
    return SectionFactory(default_bar_line_factory(tone))
