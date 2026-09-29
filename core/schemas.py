from typing import List
from typing_extensions import TypedDict


class NoteEvent(TypedDict):
    pitch: int          # MIDI pitch 0-127
    start_beat: float   # beat number, 0-indexed
    duration: float     # in beats, > 0
    velocity: int       # 1-127


class Section(TypedDict):
    name: str
    bars: int
    chords: List[str]   # one chord label per bar e.g. "Cm", "G7"


class Blueprint(TypedDict):
    key: str                    # root note e.g. "C", "F#", "Bb"
    mode: str                   # "major" or "minor"
    tempo: float                # BPM
    time_signature: List[int]   # [numerator, denominator]
    sections: List[Section]
    instruments: List[str]
