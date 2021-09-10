
from typing import Any
from yattag import Doc, indent
import re

from yattag.simpledoc import SimpleDoc

HEADER_INFO = 'header__info'
SECTION_SEPARATION = 'sections__separation'
SECTION_NAME = 'section__name'
SECTION_EMPTY_NAME = 'section__empty__name'
SECTION_REPEAT = 'section__repeat'
LINE_BAR_COMMENT = 'line__bar__comment'
LINE_BAR_REPEAT = 'line__bar__repeat'
RIFF = 'riff'
RIFF_EMPTY = 'riff--empty'
BAR_EMPTY = 'bar--empty'
BAR_ITEM = 'bar__item'
BAR_OPEN = 'bar__open'


class Tone:
    def __init__(self, key: str) -> None:
        self.set_key(key)

    def get_tone(self) -> str:
        return self.key

    def set_key(self, key: str):
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

    def deg_to_note(self, deg: int) -> str:
        return self.key_map[(deg + self.get_key_deg()) % 12]

    def note_to_deg(self, note_str: str) -> int:
        deg = self.key_map_bemol.index(
            note_str) if note_str in self.key_map_bemol else self.key_map_sharp.index(note_str)
        return (deg - self.get_key_deg()) % 12

    def is_note(self, str) -> bool:
        return str in self.key_map_bemol or str in self.key_map_sharp


class Note():
    def __init__(self, tone: Tone, deg: int) -> None:
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
    def get_content(self) -> str:
        return str(self)


class EmptyMusicElement(MusicElement):
    def __init__(self) -> None:
        super().__init__()


class StrMusicElement(MusicElement):
    def __init__(self, content: str) -> None:

        super().__init__()
        self.content = content

    def __str__(self) -> str:
        return self.content


class Chord(MusicElement):
    def __init__(self,
                 note: Note,
                 chord_type: str = "",
                 bass_note: Note = None) -> None:

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


class Riff:
    def __init__(self,
                 notes: 'list[Note]',
                 duration: int,
                 is_first_in_bar: bool) -> None:

        self.notes = notes
        self.duration = duration
        self.is_first_in_bar = is_first_in_bar

    def is_empty(self) -> bool:
        return len(self.notes) == 0

    def __str__(self) -> str:
        return ' '.join([str(n) for n in self.notes])

    def to_html(self, doc: SimpleDoc = None, tag: Any = None, text: Any = None) -> str:

        if doc == None:
            doc, tag, text = Doc().tagtext()

        kl = RIFF_EMPTY if not self.notes else ' '
        kl += ' ' + RIFF
        with tag('td', ('colspan', self.duration), klass=kl):
            text(str(self))
        return indent(doc.getvalue())


class MusicItem:
    def __init__(self,
                 duration: int,
                 music_element: MusicElement,
                 resolution: int,
                 is_first_in_bar: bool,
                 riff: Riff = None) -> None:

        self.music_element = music_element
        self.duration = duration
        self.resolution = resolution
        self.is_first_in_bar = is_first_in_bar
        self.riff = riff if riff != None else Riff(
            [], duration, is_first_in_bar)

    def get_duration(self) -> int:
        return self.duration

    def has_riff(self) -> bool:
        return not self.riff.is_empty()

    def __str__(self) -> str:
        return str(self.music_element.get_content() + '->' + str(self.riff))

    def to_html(self,
                doc: SimpleDoc = None, tag: Any = None, text: Any = None,
                riff_line: bool = False) -> str:

        if doc == None:
            doc, tag, text = Doc().tagtext()

        if riff_line:
            self.riff.to_html(doc, tag, text)
        else:
            for j in range(self.duration):
                kl = (
                    BAR_OPEN + ' ') if self.is_first_in_bar and j == 0 else ''
                kl += BAR_EMPTY if self.music_element == None else BAR_ITEM
                with tag('td', klass=kl):
                    if j == 0 and self.music_element != None:
                        text(str(self.music_element.get_content()))
        return indent(doc.getvalue())


class MusicItemFactory:
    def __init__(self, tone: Tone, resolution: int = 4) -> None:
        self.tone = tone
        self.duration = resolution
        self.resolution = resolution

    def parse_duration(self, str: str) -> str:
        dur = str[:1]
        self.duration = self.resolution
        if (dur in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]):
            self.duration = int(dur)
            return str[1:]
        return str

    def identify_note(self, str: str) -> 'tuple[int, str]':
        key = re.findall('[A-G][#b]|[A-G]', str)
        if not key or not self.tone.is_note(key[0]):
            return None, str
        deg = self.tone.note_to_deg(key[0])
        return deg, str[len(key[0]):]

    def parse_melody(self, str: str, is_first_in_bar: bool) -> Riff:
        return Riff(
            [] if str == '' else
            [Note(self.tone, self.tone.note_to_deg(st))
             for st in str.split(' ')],
            self.duration, is_first_in_bar)

    def parse(self, str: str, is_first_in_bar: bool) -> MusicItem:
        content = self.parse_duration(str)

        melody_str = re.findall('\[.*\]', content)
        riff = self.parse_melody(
            melody_str[0][1:-1] if melody_str else '', is_first_in_bar)
        element_str = content.split('[')[0]

        dash = element_str.find("/")
        music_element = None
        if dash != -1:
            n1, n2 = element_str.split("/")
            deg, chord_type = self.identify_note(n1)
            deg_bass, unused = self.identify_note(n2)
            if deg == None or deg_bass == None:
                music_element = StrMusicElement(element_str)
            else:
                music_element = Chord(
                    Note(self.tone, deg), chord_type, Note(self.tone, deg_bass))
        else:
            deg, chord_type = self.identify_note(element_str)
            if deg == None:
                music_element = StrMusicElement(element_str)
            else:
                music_element = Chord(Note(self.tone, deg), chord_type)
        return MusicItem(self.duration, music_element, self.resolution, is_first_in_bar, riff)


class Bar:
    def __init__(self, music_items: 'list[MusicItem]', bar_resolution: int) -> None:
        self.music_items = music_items
        self.bar_resolution = bar_resolution

    def __str__(self) -> str:
        return " ".join([str(mi) for mi in self.music_items])

    def has_riff(self) -> bool:
        for mi in self.music_items:
            if mi.has_riff():
                return True
        return False

    def to_html(self,
                doc: SimpleDoc = None, tag: Any = None, text: Any = None,
                riff_line: bool = False) -> str:

        if doc == None:
            doc, tag, text = Doc().tagtext()
        for mi in self.music_items:
            mi.to_html(doc, tag, text, riff_line)
        return indent(doc.getvalue())


class BarFactory:
    def __init__(self,
                 music_item_factory: MusicItemFactory,
                 resolution: int = 4) -> None:

        self.music_item_factory = music_item_factory
        self.resolution = resolution

    def parse(self, music_items_str: str) -> Bar:
        music_items = re.findall('\S*\[[^\[]*\]|\S+', music_items_str)
        return Bar(
            [MusicItem(self.resolution, None, self.resolution, True)] if not music_items else [
                self.music_item_factory.parse(st, i == 0) for i, st in enumerate(music_items)],
            self.resolution)


class BarLine:
    def __init__(self,
                 bars: 'list[Bar]',
                 comment: str = "",
                 repeat: int = 1) -> None:

        self.bars = bars
        self.comment = comment
        self.repeat = repeat

    def __str__(self) -> str:
        return self.comment + ' ' +\
            str([str(bar) for bar in self.bars]) +\
            ' x' + str(self.repeat)

    def has_riff(self) -> bool:
        for bar in self.bars:
            if bar.has_riff():
                return True
        return False

    def to_html(self,
                doc: SimpleDoc = None, tag: Any = None, text: Any = None,
                riff_line = False) -> str:

        if doc == None:
            doc, tag, text = Doc().tagtext()

        row_span = ('rowspan', '2') if self.has_riff() else ('rowspan', '1')
        write_first_line_content = riff_line or not self.has_riff()
        if write_first_line_content:
            with tag('td', row_span, klass = LINE_BAR_COMMENT):
                text(self.comment)
        for bar in self.bars:
            bar.to_html(doc, tag, text, riff_line)
        if write_first_line_content:
            with tag('td', row_span, klass = LINE_BAR_REPEAT):
                if self.repeat != 1:
                    text('x' + str(self.repeat))
        return indent(doc.getvalue())


class BarLineFactory:
    def __init__(self, bar_factory: BarFactory) -> None:
        self.bar_factory = bar_factory

    def parse(self, bar_line_str: str) -> BarLine:
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
    def __init__(self,
                 name: str,
                 repeat: int,
                 bar_lines: 'list[BarLine]') -> None:
        self.name = name
        self.bar_lines = bar_lines
        self.repeat = repeat

    def __str__(self) -> str:
        back = '\n'
        return f"{self.name} {back.join([str(lb) for lb in self.bar_lines])} x{self.repeat}"

    def count_lines(self) -> int:
        i = 0
        for bl in self.bar_lines:
            i += 2 if bl.has_riff() else 1
        return i

    def to_html(self, doc: SimpleDoc = None, tag: Any = None, text: Any = None) -> str:
        if doc == None:
            doc, tag, text = Doc().tagtext()

        row_span = ('rowspan', str(max([1, self.count_lines()])))
        # with tag('table'):
        with tag('tr'):
            with tag('td', row_span,
                     klass=SECTION_NAME + ((' ' + SECTION_EMPTY_NAME) if self.name == '' else '')):
                text(self.name)
            if self.bar_lines:
                self.bar_lines[0].to_html(
                    doc, tag, text, self.bar_lines[0].has_riff())
            if self.repeat != 1:
                with tag('td', row_span, klass=SECTION_REPEAT):
                    text("x" + str(self.repeat))
        if self.bar_lines:
            if self.bar_lines[0].has_riff():
                with tag('tr'):
                    self.bar_lines[0].to_html(doc, tag, text, False)
            for line in self.bar_lines[1:]:
                if line.has_riff():
                    with tag('tr'):
                        line.to_html(doc, tag, text, True)
                with tag('tr'):
                    line.to_html(doc, tag, text, False)

        return indent(doc.getvalue())


class SectionFactory:
    def __init__(self, bar_line_factory: BarLineFactory) -> None:
        self.bar_line_factory = bar_line_factory

    def parse(self, section_str: str) -> Section:
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
        return Section(name, repeat, [self.bar_line_factory.parse(st) for st in section_content[1:]])


class Song:
    def __init__(self,
                 title: str,
                 tone: Tone,
                 time: str,
                 tempo: int,
                 sections: 'list[Section]') -> None:

        self.title = title
        self.time = time
        self.tempo = tempo
        self.tone = tone
        self.sections = sections

    def set_key(self, key: str):
        self.tone.set_key(key)

    def to_html(self, doc: SimpleDoc = None, tag: Any = None, text: Any = None) -> str:
        if doc == None:
            doc, tag, text = Doc().tagtext()

        doc.asis('<!DOCTYPE html>')
        with tag('html'):
            with tag('head'):
                doc.stag('link', ('rel', "stylesheet"), ('href', 'style.css'))

            with tag('body'):
                with tag('h1'):
                    text(self.title)
                with tag('p', klass=HEADER_INFO):
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
                        with tag('tr', klass=SECTION_SEPARATION):
                            continue

        return indent(doc.getvalue())


class SongFactory:
    def parse(self,
              str: str,
              section_factory: SectionFactory = None,
              bar_resolution: int = 4):

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


def default_music_item_factory(tone: Tone):
    return MusicItemFactory(tone)


def default_bar_factory(tone: Tone):
    return BarFactory(default_music_item_factory(tone))


def default_bar_line_factory(tone: Tone):
    return BarLineFactory(default_bar_factory(tone))


def default_section_factory(tone: Tone):
    return SectionFactory(default_bar_line_factory(tone))
