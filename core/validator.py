from typing import List

NOTE_TO_PC = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}

SCALE_INTERVALS = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
}

# Allowed MIDI pitch range per instrument role
PITCH_RANGES = {
    "drums":  (35, 81),
    "bass":   (28, 60),
    "chords": (36, 96),
    "melody": (48, 96),
}


def key_pitch_classes(key: str, mode: str) -> set:
    root = NOTE_TO_PC[key]
    return {(root + i) % 12 for i in SCALE_INTERVALS[mode]}


def total_beats(blueprint: dict) -> float:
    beats_per_bar = blueprint["time_signature"][0]
    return sum(sec["bars"] for sec in blueprint["sections"]) * beats_per_bar


def validate_note_event(ev: dict) -> List[str]:
    errors = []
    for field in ("pitch", "start_beat", "duration", "velocity"):
        if field not in ev:
            errors.append(f"NoteEvent missing field: {field}")
    if "pitch" in ev and not (0 <= ev["pitch"] <= 127):
        errors.append(f"pitch {ev['pitch']} out of range 0-127")
    if "velocity" in ev and not (1 <= ev["velocity"] <= 127):
        errors.append(f"velocity {ev['velocity']} out of range 1-127")
    if "duration" in ev and ev["duration"] <= 0:
        errors.append(f"duration must be > 0, got {ev['duration']}")
    if "start_beat" in ev and ev["start_beat"] < 0:
        errors.append(f"start_beat must be >= 0, got {ev['start_beat']}")
    return errors


def validate_notes_in_range(instrument: str, notes: List[dict]) -> List[str]:
    if instrument not in PITCH_RANGES:
        return []
    lo, hi = PITCH_RANGES[instrument]
    return [
        f"{instrument} pitch {ev['pitch']} out of range [{lo}, {hi}]"
        for ev in notes if not (lo <= ev["pitch"] <= hi)
    ]


def validate_notes_in_key(instrument: str, notes: List[dict], key: str, mode: str) -> List[str]:
    if instrument == "drums":
        return []
    pcs = key_pitch_classes(key, mode)
    return [
        f"{instrument} pitch {ev['pitch']} (class {ev['pitch'] % 12}) not in {key} {mode}"
        for ev in notes if ev["pitch"] % 12 not in pcs
    ]


def validate_bar_lengths(instrument: str, notes: List[dict], song_beats: float) -> List[str]:
    return [
        f"{instrument} note ends at beat {ev['start_beat'] + ev['duration']:.2f}, "
        f"beyond song length {song_beats}"
        for ev in notes if ev["start_beat"] + ev["duration"] > song_beats + 1e-6
    ]


def validate_no_overlaps(instrument: str, notes: List[dict]) -> List[str]:
    if instrument == "drums":
        return []
    errors = []
    last: dict = {}
    for ev in sorted(notes, key=lambda e: e["start_beat"]):
        p = ev["pitch"]
        if p in last:
            prev_end = last[p]["start_beat"] + last[p]["duration"]
            if ev["start_beat"] < prev_end - 1e-6:
                errors.append(
                    f"{instrument} pitch {p} overlaps at beat {ev['start_beat']:.2f}"
                )
        last[p] = ev
    return errors


def validate_blueprint(bp: dict) -> List[str]:
    errors = []
    for field in ("key", "mode", "tempo", "time_signature", "sections", "instruments"):
        if field not in bp:
            errors.append(f"Blueprint missing field: {field}")
    if "key" in bp and bp["key"] not in NOTE_TO_PC:
        errors.append(f"Unknown key: {bp['key']}")
    if "mode" in bp and bp["mode"] not in SCALE_INTERVALS:
        errors.append(f"Unknown mode: {bp['mode']}")
    if "time_signature" in bp:
        ts = bp["time_signature"]
        if not (isinstance(ts, list) and len(ts) == 2
                and all(isinstance(x, int) and x > 0 for x in ts)):
            errors.append(f"time_signature must be [int, int] with positive values, got {ts}")
    if "sections" in bp:
        for i, sec in enumerate(bp["sections"]):
            for field in ("name", "bars", "chords"):
                if field not in sec:
                    errors.append(f"Section {i} missing field: {field}")
            if "bars" in sec and "chords" in sec and len(sec["chords"]) != sec["bars"]:
                errors.append(
                    f"Section '{sec.get('name', i)}': "
                    f"{len(sec['chords'])} chords but {sec['bars']} bars"
                )
    return errors


def validate_part(instrument: str, notes: List[dict], blueprint: dict) -> List[str]:
    """Full validation of one instrument's notes against the blueprint."""
    errors = []
    for ev in notes:
        errors.extend(validate_note_event(ev))
    errors.extend(validate_notes_in_range(instrument, notes))
    errors.extend(validate_notes_in_key(instrument, notes, blueprint["key"], blueprint["mode"]))
    errors.extend(validate_bar_lengths(instrument, notes, total_beats(blueprint)))
    errors.extend(validate_no_overlaps(instrument, notes))
    return errors
