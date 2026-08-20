import struct
from pathlib import Path

from cura_time_analyzer.inputs import read_gcode_lines


def test_read_gx_extracts_embedded_gcode(tmp_path: Path):
    payload = b"xgcode 1.0\n" + b"\0" * 6
    gcode_offset = 64
    payload += b"\0" * (gcode_offset - len(payload))
    payload += b";LAYER:0\nG1 X1 Y1 F600\n"
    payload = bytearray(payload)
    struct.pack_into("<I", payload, 0x14, gcode_offset)
    struct.pack_into("<I", payload, 0x18, gcode_offset)
    path = tmp_path / "sample.gx"
    path.write_bytes(payload)

    lines, metadata = read_gcode_lines(path)

    assert lines == [";LAYER:0", "G1 X1 Y1 F600"]
    assert metadata["format"] == "gx"
    assert metadata["gcode_offset"] == gcode_offset
