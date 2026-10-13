#!/usr/bin/env python3
"""Functional tests for the assrender VapourSynth plugin.

Usage: python3 test/test_assrender.py [path/to/libassrender.so]

Without an argument the plugin is expected to be autoloaded (e.g. from the
installed wheel) or to be found in site-packages/vapoursynth/plugins.

Requires the vapoursynth Python module (R55 or newer).
"""
import glob
import os
import sys
import tempfile

import vapoursynth as vs

core = vs.core

ASS = """[Script Info]
ScriptType: v4.00+
PlayResX: 320
PlayResY: 240

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,40,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,Hello
Dialogue: 0,0:00:02.00,0:00:03.00,Default,,0,0,0,,World
"""


def load_plugin(args):
    if args:
        core.std.LoadPlugin(args[0])
        return
    if hasattr(core, "assrender"):
        return
    # Wheel layout: site-packages/vapoursynth/plugins/<plugin>
    plugin_dir = os.path.join(os.path.dirname(vs.__file__), "plugins")
    for ext in ("so", "dll", "dylib"):
        for path in glob.glob(os.path.join(plugin_dir, "**", "*assrender." + ext), recursive=True):
            core.std.LoadPlugin(path)
            return
    raise SystemExit("FAIL: assrender plugin is neither autoloaded nor found below " + plugin_dir)


def check(cond, msg):
    if not cond:
        raise SystemExit("FAIL: " + msg)
    print("ok  ", msg)


def expect_error(fn, msg, contains=""):
    try:
        fn()
    except vs.Error as e:
        text = str(e).strip().splitlines()[-1]
        check(contains in text, "%s (%s)" % (msg, text))
    else:
        raise SystemExit("FAIL: no error raised: " + msg)


def changed(a, b, n):
    """Largest difference of plane 0 between frame n of a and b."""
    return core.std.PlaneStats(a, b, plane=0).get_frame(n).props["PlaneStatsDiff"]


def main():
    load_plugin(sys.argv[1:])
    check(hasattr(core, "assrender"), "plugin loaded (namespace assrender)")

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test.ass")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(ASS)

        # 25 fps: frames 0-24 show "Hello", 25-49 nothing, 50-74 "World".
        for fmt in (vs.YUV420P8, vs.YUV420P10, vs.YUV422P8, vs.YUV444P16, vs.RGB24, vs.RGB48, vs.GRAY8, vs.GRAY16):
            src = core.std.BlankClip(width=320, height=240, format=fmt, length=80, fpsnum=25, fpsden=1)
            out = core.assrender.TextSub(src, file=path)
            name = core.get_video_format(fmt).name
            check(out.format.id == src.format.id and out.num_frames == 80, "%s: format and length kept" % name)
            check(changed(src, out, 10) > 0 and changed(src, out, 35) == 0 and changed(src, out, 60) > 0,
                  "%s: text only while a dialogue line is active" % name)

        src = core.std.BlankClip(width=320, height=240, format=vs.YUV420P8, length=50, fpsnum=25, fpsden=1)
        out = core.assrender.Subtitle(src, text=["Plain text"], start=[10], end=[20])
        check(changed(src, out, 5) == 0 and changed(src, out, 15) > 0 and changed(src, out, 30) == 0, "Subtitle: text between start and end")

        expect_error(lambda: core.assrender.TextSub(src, file=os.path.join(tmp, "missing.ass")), "missing file rejected", "does not exist")
        expect_error(lambda: core.assrender.TextSub(src.resize.Point(format=vs.YUV420PS), file=path), "32 bit float rejected", "32")
        expect_error(lambda: core.assrender.TextSub(src, file=path, hinting=7), "hinting 7 rejected", "hinting")

    print("all tests passed")


if __name__ == "__main__":
    main()
