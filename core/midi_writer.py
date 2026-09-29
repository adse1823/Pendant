import os
import pretty_midi

# General MIDI program numbers per instrument role
_PROGRAMS = {
    "bass":   33,  # Electric Bass (finger)
    "chords":  0,  # Acoustic Grand Piano
    "melody":  0,  # Acoustic Grand Piano
}


def write_midi(song: dict, path: str) -> None:
    """Write a song dict to a MIDI file.

    song = {
        "tempo": 80,
        "instruments": {
            "drums":  [{"pitch": int, "start_beat": float, "duration": float, "velocity": int}, ...],
            "bass":   [...],
            "chords": [...],
            "melody": [...],
        }
    }
    """
    tempo = float(song.get("tempo", 120))
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    spb = 60.0 / tempo  # seconds per beat

    for name, events in song["instruments"].items():
        is_drum = name == "drums"
        program = 0 if is_drum else _PROGRAMS.get(name, 0)
        track = pretty_midi.Instrument(program=program, is_drum=is_drum, name=name)
        for ev in events:
            start = ev["start_beat"] * spb
            end = start + max(ev["duration"], 0.01) * spb
            track.notes.append(pretty_midi.Note(
                velocity=int(ev["velocity"]),
                pitch=int(ev["pitch"]),
                start=start,
                end=end,
            ))
        midi.instruments.append(track)

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    midi.write(path)


if __name__ == "__main__":
    # Sample 2-bar lo-fi beat at 80 BPM — kick/snare/hi-hat + bass
    sample = {
        "tempo": 80,
        "instruments": {
            "drums": [
                # kick on beats 1 and 3
                {"pitch": 36, "start_beat": 0,   "duration": 0.25, "velocity": 100},
                {"pitch": 36, "start_beat": 2,   "duration": 0.25, "velocity": 100},
                {"pitch": 36, "start_beat": 4,   "duration": 0.25, "velocity": 100},
                {"pitch": 36, "start_beat": 6,   "duration": 0.25, "velocity": 100},
                # snare on beats 2 and 4
                {"pitch": 38, "start_beat": 1,   "duration": 0.25, "velocity": 80},
                {"pitch": 38, "start_beat": 3,   "duration": 0.25, "velocity": 80},
                {"pitch": 38, "start_beat": 5,   "duration": 0.25, "velocity": 80},
                {"pitch": 38, "start_beat": 7,   "duration": 0.25, "velocity": 80},
                # closed hi-hat every half beat
                *[{"pitch": 42, "start_beat": i * 0.5, "duration": 0.25, "velocity": 60}
                  for i in range(16)],
            ],
            "bass": [
                {"pitch": 40, "start_beat": 0, "duration": 1.5, "velocity": 90},
                {"pitch": 40, "start_beat": 2, "duration": 1.5, "velocity": 90},
                {"pitch": 43, "start_beat": 4, "duration": 1.5, "velocity": 90},
                {"pitch": 43, "start_beat": 6, "duration": 1.5, "velocity": 90},
            ],
        },
    }
    out = os.path.join(os.path.dirname(__file__), "..", "outputs", "sample.mid")
    write_midi(sample, out)
    print(f"Written: {os.path.abspath(out)}")
