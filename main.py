import sys
import os

from PyQt6.QtCore import (
    Qt,
    QUrl
)

from PyQt6.QtGui import (
    QPixmap,
    QCursor
)

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsView,
    QGraphicsScene
)

from PyQt6.QtMultimedia import (
    QMediaPlayer,
    QAudioOutput
)

from PyQt6.QtMultimediaWidgets import (
    QGraphicsVideoItem
)

from PyQt6.QtWidgets import QGraphicsPixmapItem

import config


def get_app_root():

    if hasattr(sys, "_MEIPASS"):
        return os.path.dirname(
            sys.executable
        )

    return os.path.dirname(
        os.path.abspath(__file__)
    )


class ImageButton(QGraphicsPixmapItem):

    def __init__(
        self,
        main_window,
        index,
        normal_path,
        active_path
    ):

        super().__init__()

        self.main_window = main_window

        self.index = index

        self.normal_path = normal_path

        self.active_path = active_path

        self.setAcceptHoverEvents(
            True
        )

        self.setAcceptedMouseButtons(
            Qt.MouseButton.LeftButton
        )

        self.set_normal()

    def set_normal(self):

        pixmap = QPixmap(
            self.normal_path
        )

        pixmap = pixmap.scaled(
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.setPixmap(
            pixmap
        )

    def set_active(self):

        pixmap = QPixmap(
            self.active_path
        )

        pixmap = pixmap.scaled(
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.setPixmap(
            pixmap
        )

    def hoverEnterEvent(
        self,
        event
    ):

        QApplication.setOverrideCursor(
            QCursor(
                Qt.CursorShape.PointingHandCursor
            )
        )

    def hoverLeaveEvent(
        self,
        event
    ):

        QApplication.restoreOverrideCursor()

    def mousePressEvent(
        self,
        event
    ):

        self.main_window.on_image_click(
            self.index
        )


class VideoPlayerWindow(
    QMainWindow
):

    def __init__(
        self
    ):

        super().__init__()

        self.app_root = get_app_root()

        self.loop_index = 0

        self.active_video_index = None

        self.image_buttons = []

        # 断点功能：记录主循环被打断时的位置
        self.saved_loop_index = 0

        self.saved_position = 0

        # 是否处于"被打断"状态（有一个有效的断点待恢复）
        self.is_interrupted = False

        # 待恢复的播放位置，在媒体加载完成后统一应用
        self._pending_position = 0

        self.init_ui()

        self.init_player()

        self.return_home()

    def init_ui(
        self
    ):

        self.setWindowTitle(
            "Video Player"
        )

        self.resize(
            config.SCREEN_WIDTH,
            config.SCREEN_HEIGHT
        )

        self.scene = QGraphicsScene()

        self.view = QGraphicsView(
            self.scene,
            self
        )

        self.setCentralWidget(
            self.view
        )

        self.view.setFrameShape(
            self.view.Shape.NoFrame
        )

        self.view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.view.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scene.setSceneRect(
            0,
            0,
            config.SCREEN_WIDTH,
            config.SCREEN_HEIGHT
        )

        # 视频层
        self.video_item = QGraphicsVideoItem()

        self.video_item.setSize(
            self.scene.sceneRect().size()
        )

        self.scene.addItem(
            self.video_item
        )

        self.create_buttons()

    def create_buttons(
        self
    ):

        image_dir = os.path.join(
            self.app_root,
            "image"
        )

        total_width = (
            len(config.BUTTON_IMAGES)
            * config.BUTTON_WIDTH
            +
            (
                len(config.BUTTON_IMAGES)
                - 1
            )
            * config.BUTTON_SPACING
        )

        start_x = (
            config.SCREEN_WIDTH
            - total_width
        ) // 2

        for i in range(
            len(
                config.BUTTON_IMAGES
            )
        ):

            normal_path = os.path.join(
                image_dir,
                config.BUTTON_IMAGES[i]
            )

            active_path = os.path.join(
                image_dir,
                config.BUTTON_IMAGES_ACTIVE[i]
            )

            btn = ImageButton(
                self,
                i,
                normal_path,
                active_path
            )

            btn.setPos(
                start_x
                +
                i
                * (
                    config.BUTTON_WIDTH
                    +
                    config.BUTTON_SPACING
                ),
                config.BUTTON_Y
            )

            self.scene.addItem(
                btn
            )

            self.image_buttons.append(
                btn
            )

    def init_player(
        self
    ):

        self.media_player = QMediaPlayer()

        self.audio_output = QAudioOutput()

        self.media_player.setAudioOutput(
            self.audio_output
        )

        self.audio_output.setVolume(
            config.INIT_VOLUME / 100
        )

        self.media_player.setVideoOutput(
            self.video_item
        )

        self.media_player.mediaStatusChanged.connect(
            self.on_media_status_changed
        )

    def play_video(
        self,
        filename,
        position=0
    ):

        path = os.path.join(
            self.app_root,
            filename
        )

        self.media_player.setSource(
            QUrl.fromLocalFile(path)
        )

        # 记录待恢复位置，在 LoadedMedia 时统一应用并播放
        self._pending_position = position

        if self.active_video_index is None:
            self.update_loop_highlight()

    def clear_all_highlights(
        self
    ):

        for btn in self.image_buttons:

            btn.set_normal()

    def highlight_button(
        self,
        index
    ):

        self.clear_all_highlights()

        self.image_buttons[
            index
        ].set_active()

    def update_loop_highlight(
        self
    ):

        self.clear_all_highlights()

        # videoA
        if self.loop_index == 0:
            return

        btn_index = (
            self.loop_index - 1
        )

        if (
            0
            <=
            btn_index
            <
            len(self.image_buttons)
        ):

            self.image_buttons[
                btn_index
            ].set_active()

    def return_home(
        self
    ):

        self.active_video_index = None

        self.loop_index = 0

        self.is_interrupted = False

        self.clear_all_highlights()

        self.play_video(
            config.LOOP_VIDEOS[0]
        )

    def resume_loop_video(
        self
    ):

        self.active_video_index = None

        self.loop_index = (
            self.saved_loop_index
        )

        self.is_interrupted = False

        self.play_video(
            config.LOOP_VIDEOS[
                self.loop_index
            ],
            self.saved_position
        )

    def on_image_click(
        self,
        index
    ):

        # 再次点击当前分视频按钮：结束分视频，回到断点位置
        if (
            self.active_video_index
            ==
            index
        ):

            if self.is_interrupted:
                self.resume_loop_video()
            else:
                self.return_home()

            return

        # 只有从主循环模式打断时才保存断点
        # 从一个分视频切换到另一个分视频时，保持原有断点不被覆盖
        if self.active_video_index is None:

            self.saved_loop_index = (
                self.loop_index
            )

            self.saved_position = (
                self.media_player.position()
            )

            self.is_interrupted = True

        self.active_video_index = index

        self.highlight_button(
            index
        )

        self.play_video(
            config.LOOP_VIDEOS[
                index + 1
            ]
        )

    def on_media_status_changed(
        self,
        status
    ):

        # 媒体加载完成：应用待恢复位置并开始播放
        if (
            status
            ==
            QMediaPlayer.MediaStatus.LoadedMedia
        ):

            if self._pending_position > 0:
                self.media_player.setPosition(
                    self._pending_position
                )

            self.media_player.play()

            self._pending_position = 0

            return

        if (
            status
            !=
            QMediaPlayer.MediaStatus.EndOfMedia
        ):
            return

        # 分视频结束（自然播放完）
        if (
            self.active_video_index
            is not None
        ):

            if self.is_interrupted:
                self.resume_loop_video()
            else:
                self.return_home()

            return

        # 主循环：播放下一个视频
        self.loop_index += 1

        if (
            self.loop_index
            >=
            len(
                config.LOOP_VIDEOS
            )
        ):

            self.loop_index = 0

        self.play_video(
            config.LOOP_VIDEOS[
                self.loop_index
            ]
        )

    def mouseDoubleClickEvent(
            self,
            event
        ):

            if self.isFullScreen():

                self.showNormal()

            else:

                self.showFullScreen()


if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    window = VideoPlayerWindow()

    window.showFullScreen()

    sys.exit(
        app.exec()
    )
