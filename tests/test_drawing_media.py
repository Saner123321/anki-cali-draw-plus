import json
import unittest

from drawing_media import drawing_refs, load_scene, media_name


def svg(model):
    return (f'<svg xmlns="http://www.w3.org/2000/svg"><metadata id="cali-draw-plus">'
            f'{json.dumps(model)}</metadata></svg>').encode()


class DrawingMediaTest(unittest.TestCase):
    def test_reload_raw_and_smoothed_pressure(self):
        pen = {"t": "pen", "c": "auto", "w": 3, "p": [[-10, 20, .2, .2], [5, 25, .5, .8]], "pen": True, "ps": .7}
        markup = svg({"version": 1, "strokes": [pen]})
        self.assertEqual(json.loads(load_scene(markup)), [pen])
        self.assertEqual(media_name(markup), media_name(markup))
        self.assertNotEqual(media_name(svg({"version": 1, "strokes": []})), media_name(markup))

    def test_reject_invalid_format_or_scene(self):
        for data in (b'<svg/>', svg({"version": 2, "strokes": []}),
                     svg({"version": 1, "strokes": [{"t": "arrow", "c": "auto", "w": 3, "p": [[0, 0]]}]}),
                     svg({"version": 1, "strokes": [{"t": "pen", "c": "auto", "w": 3, "p": [[0, 0, .1, 2]]}]})):
            with self.subTest(data=data), self.assertRaises(ValueError):
                load_scene(data)

    def test_replace_only_the_selected_occurrence(self):
        old, new = media_name(b"old"), media_name(b"new")
        first = f'<img SRC="{old}" width=180 title=" src=ignore">'
        second = f"<img class='fit' src='{old}'>"
        field = f"题目{first}\n<!-- {second} -->{second}<b>保留</b>"
        a, b = drawing_refs("Back", field)
        self.assertEqual(a.occurrence, 0)
        self.assertEqual(b.replace(field, new), f"题目{first}\n<!-- {second} -->{second.replace(old, new)}<b>保留</b>")
        with self.assertRaises(ValueError):
            b.replace(field + "changed", new)

    def test_unique_reference_survives_surrounding_edits(self):
        old, new = media_name(b"old"), media_name(b"new")
        ref = drawing_refs("Back", f"<img src={old}>")[0]
        self.assertEqual(ref.replace(f"<b>new text</b><img width='80' src={old}>", new),
                         f"<b>new text</b><img width='80' src={new}>")
        with self.assertRaises(ValueError):
            ref.replace(f"<img src={new}>", new)


if __name__ == "__main__":
    unittest.main()
