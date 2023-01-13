# ----------------------------------------------------------------------------
# -                        Open3D: www.open3d.org                            -
# ----------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2018-2021 www.open3d.org
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
# ----------------------------------------------------------------------------

# Reference: https://github.com/isl-org/Open3D/blob/73508bcaba0a9a31e398bf8de76e3bbeaed81540/examples/python/visualization/video.py
import numpy as np
import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import time
import threading


def rescale_greyscale(img):
    data = np.asarray(img)
    assert (len(data.shape) == 2)  # requires 1 channel image
    dataFloat = data.astype(np.float64)
    max_val = dataFloat.max()
    # We don't currently support 16-bit images, so convert to 8-bit
    dataFloat *= 255.0 / max_val
    data8 = dataFloat.astype(np.uint8)
    return o3d.geometry.Image(data8)


class VideoWindow:

    def __init__(self, img, depth, lidar):

        self.window = gui.Application.instance.create_window(
            "Open3D - Video Example", 1000, 500)
        self.window.set_on_layout(self._on_layout)
        self.window.set_on_close(self._on_close)

        self.widget3d = gui.SceneWidget()
        self.widget3d.scene = rendering.Open3DScene(self.window.renderer)
        self.window.add_child(self.widget3d)

        # lit = rendering.MaterialRecord()
        # lit.shader = "defaultLit"
        # self.widget3d.scene.add_geometry(lidar)
        bounds = self.widget3d.scene.bounding_box
        self.widget3d.setup_camera(60.0, bounds, bounds.get_center())
        self.widget3d.scene.show_axes(True)

        em = self.window.theme.font_size
        margin = 0.5 * em
        self.panel = gui.Vert(0.5 * em, gui.Margins(margin))
        self.panel.add_child(gui.Label("Color image"))
        self.rgb_widget = gui.ImageWidget(img)
        self.panel.add_child(self.rgb_widget)
        self.panel.add_child(gui.Label("Depth image (normalized)"))
        self.depth_widget = gui.ImageWidget(depth)
        self.panel.add_child(self.depth_widget)
        self.window.add_child(self.panel)

        self.is_done = False
        threading.Thread(target=self._update_thread).start()

    def _on_layout(self, layout_context):
        contentRect = self.window.content_rect
        panel_width = 15 * layout_context.theme.font_size  # 15 ems wide
        self.widget3d.frame = gui.Rect(contentRect.x, contentRect.y,
                                       contentRect.width - panel_width,
                                       contentRect.height)
        self.panel.frame = gui.Rect(self.widget3d.frame.get_right(),
                                    contentRect.y, panel_width,
                                    contentRect.height)

    def _on_close(self):
        self.is_done = True
        return True  # False would cancel the close

    def _update_thread(self, img, depth, lidar):
        # This is NOT the UI thread, need to call post_to_main_thread() to update
        # the scene or any part of the UI.
        time.sleep(0.100)

        # Get the next frame, for instance, reading a frame from the camera.
        rgb_frame = img
        depth_frame = depth

        # Update the images. This must be done on the UI thread.
        def update():
            self.rgb_widget.update_image(rgb_frame)
            self.depth_widget.update_image(depth_frame)
            # self.widget3d.scene.add_geometry(lidar)

        gui.Application.instance.post_to_main_thread(self.window, update)
