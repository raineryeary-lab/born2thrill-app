"""An upper storey's OWN outline traces the outer face; it must snap onto the
ground floor's OUTER faces, not the inner-face lines that room edges snap to
(twostorey_050, 2026-09-19: OG came out 240 mm inside the EG on every side)."""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "plan_builder", os.path.join(HERE, "build-simplifier-render-plan.py"))
plan_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_builder)

RegisteredFrame = plan_builder.RegisteredFrame
Frame = plan_builder.Frame


def identity_frame(x_inner, y_inner, x_outer, y_outer, own_points):
    ground = Frame(10.0, 1000, 1000)                 # 10 m wide, 10 m tall, y flipped
    affine = (1.0, 0.0, 1.0, 0.0)                    # OG coordinates == ground coordinates
    return RegisteredFrame(ground, affine, x_inner, y_inner, own_points,
                           outline_x_lines=x_outer, outline_y_lines=y_outer)


class OutlineSnapTests(unittest.TestCase):
    def test_outline_points_snap_to_outer_faces_not_inner_faces(self):
        # ground outer faces at x=1000/9000 mm, inner faces 240 mm further in
        frame = identity_frame([1240.0, 8760.0], [1240.0, 8760.0],
                               [1000.0, 9000.0], [1000.0, 9000.0], [])
        square = [{"x": 0.104, "y": 0.104}, {"x": 0.896, "y": 0.104},
                  {"x": 0.896, "y": 0.896}, {"x": 0.104, "y": 0.896}]
        out = frame.outline_polygon(square)
        xs = sorted({p[0] for p in out})
        self.assertEqual(xs, [1000.0, 9000.0])       # flush with the EG's outer face

    def test_room_points_still_use_the_inner_face_lines(self):
        own = [{"x": 0.124, "y": 0.5}, {"x": 0.876, "y": 0.5}]
        ground = Frame(10.0, 1000, 1000)
        frame = RegisteredFrame(ground, (1.0, 0.0, 1.0, 0.0), [1240.0, 8760.0], [], own,
                                outline_x_lines=[1000.0, 9000.0], outline_y_lines=[])
        self.assertEqual(frame.point({"x": 0.124, "y": 0.5})[0], 1240.0)

    def test_a_real_setback_beyond_the_snap_range_is_kept(self):
        frame = identity_frame([1240.0], [], [1000.0], [], [])
        pts = [{"x": 0.30, "y": 0.2}, {"x": 0.9, "y": 0.2}, {"x": 0.9, "y": 0.8}, {"x": 0.30, "y": 0.8}]
        out = frame.outline_polygon(pts)
        self.assertAlmostEqual(min(p[0] for p in out), 3000.0, places=1)

    def test_ground_frame_has_no_outline_polygon_method(self):
        self.assertFalse(hasattr(Frame(10.0, 1000, 1000), "outline_polygon"))


if __name__ == "__main__":
    unittest.main()
