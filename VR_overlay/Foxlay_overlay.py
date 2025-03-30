import sys,time,traceback,os
import requests
from PIL import Image,ImageQt
from io import BytesIO
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSpacerItem, QSizePolicy,QPushButton,QMessageBox
from PyQt6.QtGui import QPixmap, QPainter, QColor,QImage
from PyQt6.QtCore import Qt, QByteArray, QUrl,QEvent
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json

class WatchdogEvent(QEvent):
    """Кастомное событие для передачи данных в основной поток"""
    def __init__(self, message):
        super().__init__(QEvent.Type(UserEventType))  # Используем кастомный тип события
        self.message = message

class NewFolderEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            with open("/tmp/discover_overlay_api.json","r") as f:
                try:
                    data=json.load(f)
                    self.mainWindow.trigger_watchdog_event(data)

                except json.decoder.JSONDecodeError:
                    pass
            #print("Test:", event.src_path)
            #time.sleep(5)
            #process_new_folder(event.src_path)


class TransparentWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.UsersWidget=[]

        self.in_room=[]
        self.userlist={}
        self.EventRandom=0

        if(os.path.isfile('icons/foxlay_disabled_headphone.png')):
            self.headphone = Image.open("icons/foxlay_disabled_headphone.png").resize((32,32))
            self.microphone = Image.open("icons/foxlay_disabled_microphone.png").resize((32,32))
        else:
            self.headphone = Image.open("/usr/share/icons/hicolor/512x512/apps/foxlay_disabled_headphone.png").resize((32,32))
            self.microphone = Image.open("/usr/share/icons/hicolor/512x512/apps/foxlay_disabled_microphone.png").resize((32,32))

        self.AvatarCache={}

        #os.environ["WAYLAND_DISPLAY"]="wayland-20"
        #os.environ["DISPLAY"]=""

        # Убираем рамку и включаем прозрачность
        if (os.environ.get('WAYLAND_DISPLAY') == "wayland-20"):
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setWindowTitle("Foxlay VR-Overlay")

        # Основной макет
        self.layout = QVBoxLayout(self)

        spacer_top = QSpacerItem(10, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.layout.addSpacerItem(spacer_top)

        # Верхняя граница
        #self.top_label = QLabel("======[виджет]======")
        #self.top_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #self.layout.addWidget(self.top_label)

        # Контейнер для элементов
        self.items_container = QVBoxLayout()
        self.layout.addLayout(self.items_container)

        # Нижняя граница
        #self.bottom_label = QLabel("======[виджет]======")
        #self.bottom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #self.layout.addWidget(self.bottom_label)

        # Спейсер снизу, чтобы элементы прижимались к верху
        spacer_bottom = QSpacerItem(10, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.layout.addSpacerItem(spacer_bottom)

        self.setLayout(self.layout)

        event_handler = NewFolderEventHandler()
        event_handler.mainWindow=self

        self.resize(200,400)


        self.observer = Observer()
        self.observer.schedule(event_handler, "/tmp/discover_overlay_api.json", recursive=False)
        self.observer.start()

        #self.button = QPushButton("Удалить и добавить новые")
        #self.layout.addWidget(self.button)
        #self.button.clicked.connect(self.change_widgets)

        with open("/tmp/discover_overlay_api.json","r") as f:
            data=json.load(f)
            self.in_room=data['in_room']
            self.userlist=data['userlist']
        self.update_items()

    def trigger_watchdog_event(self, message):
        # Создаем и отправляем кастомное событие в основной поток
        event = WatchdogEvent(message)
        QApplication.postEvent(self, event)


    def customEvent(self, event):
        if event.type() == QEvent.Type(UserEventType):
            # Когда событие приходит в основной поток, обновляем интерфейс

            if(self.EventRandom==event.message["random"]): # ghost event bugfix
                return
            else:
                self.EventRandom=event.message["random"]

            print("Получено событие:", event.message["event"])
            if not(len(event.message['in_room'])==len(self.in_room)):
                self.in_room=event.message['in_room']
                #print("Количество юзеров обновленно!")
            if not(event.message['userlist'] is self.userlist):
                self.userlist=event.message['userlist']
                #print("Состояние пользоваталей обновленно")
            if(event.message["event"]=="SPEAKING_START") or (event.message["event"]=="SPEAKING_STOP") or (event.message["event"]=="VOICE_STATE_UPDATE"):
                try:
                    self.update_Avatars(event.message["event"])
                except KeyError:
                    self.update_items()
                return
            self.update_items()

    def update_Avatars(self,event):
        if(event=="SPEAKING_START") or (event=="SPEAKING_STOP"):
            for user_id in self.in_room:
                if self.userlist[user_id]["speaking"]:
                    self.UserAvatars[user_id].setStyleSheet("border: 2px solid;border-color: green;")
                else:
                    self.UserAvatars[user_id].setStyleSheet("margin: 2px;")
        if(event=="VOICE_STATE_UPDATE"):
            for user_id in self.in_room:
                self.UserAvatars[user_id].setPixmap(self.load_image(user_id,
                    self.userlist[user_id]['avatar'],
                    deaf=self.userlist[user_id]['deaf'],
                    mute=self.userlist[user_id]['mute']))

        #UserAvatars

    def update_items(self):
        """Очищает виджет и добавляет новые элементы."""
        # Очистка старых элементов
        i=0

        while not len(self.UsersWidget)==i:
            layout=self.UsersWidget[i][len(self.UsersWidget[i])-1]
            for widget in self.UsersWidget[i]:
                try:
                    #print(widget)
                    widget.deleteLater()#removeItem 
                except AttributeError:
                    layout.removeItem(widget)
            i=i+1
        self.UsersWidget=[]
        self.UserAvatars={}

        # Добавляем новые элементы
        self.image_labels = {}  # Храним ссылки на QLabel для изображений

        for idx, (User_id) in enumerate(self.in_room):
            item_layout = QHBoxLayout()  # Горизонтальный макет для картинки и текста

            image_url="https://cdn.discordapp.com/avatars/"+User_id+"/"+self.userlist[User_id].get('avatar')+".png"

            # QLabel для изображения (заглушка до загрузки)
            img_label = QLabel()
            img_label.setFixedSize(34, 34)  # Размер иконки
            img_label.setPixmap(self.load_image(User_id,
                    self.userlist[User_id]['avatar'],
                    deaf=self.userlist[User_id]['deaf'],
                    mute=self.userlist[User_id]['mute']))
            self.UserAvatars[User_id]=img_label


            # QLabel для текста с прозрачным фоном
            text_label = QLabel(self.userlist[User_id].get("nick"))
            if self.userlist[User_id].get('speaking'):
                img_label.setStyleSheet("border: 2px solid;border-color: green;")
            else:
                self.UserAvatars[User_id].setStyleSheet("margin: 2px;")

            # QLabel для текста с прозрачным фоном
            text_label.setStyleSheet("background-color: rgba(0, 0, 0, 150); color: white; padding: 3px; border-radius: 0px;")

            # Спейсер для прижатия к левому краю
            spacer_right = QSpacerItem(40, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            spacer_left = QSpacerItem(40, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

            # Добавляем виджеты в горизонтальный макет
            item_layout.addSpacerItem(spacer_left)
            item_layout.addWidget(img_label)
            item_layout.addWidget(text_label)
            item_layout.addSpacerItem(spacer_right)
            self.UsersWidget.append([spacer_left,img_label,text_label,spacer_right,item_layout])
            self.items_container.addLayout(item_layout)
            #print(User_id)
        self.items_container.update()
        self.update()

    def get_placeholder_pixmap(self):
        """Создаёт заглушку для изображения."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("gray"))
        return pixmap

    def paintEvent(self, event):
        """Делаем окно полностью прозрачным"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 100))  # Полупрозрачный фон (чёрный с альфа-каналом)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        #painter = QPainter(self)
        #painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        #painter.fillRect(self.rect(), Qt.GlobalColor.transparent)

    def load_image(self,user_id,avatar_hash,deaf=False,mute=False):
        # URL изображения, которое загружаем с интернета
        url1 = "https://example.com/path/to/first_image.jpg"

        # Загрузка первого изображения
        if not(self.AvatarCache.get(avatar_hash)):
            print("loading: "+str(avatar_hash))
            response1 = requests.get("https://cdn.discordapp.com/avatars/"+user_id+"/"+avatar_hash+".png")
            self.AvatarCache[avatar_hash] = Image.open(BytesIO(response1.content)).resize((32,32)).convert("RGBA")


        if deaf:
            Avatar=self.AvatarCache[avatar_hash].copy()
            Avatar.paste(self.headphone, (0, 0), self.headphone.convert("RGBA").split()[3]) 
        elif mute:
            Avatar=self.AvatarCache[avatar_hash].copy()
            Avatar.paste(self.microphone, (0, 0), self.microphone.convert("RGBA").split()[3]) 
        else:
            Avatar=self.AvatarCache[avatar_hash]


        # Загрузка второго изображения (наложение)
        #response2 = requests.get(url2)
        #image2 = Image.open("")

        # Масштабируем изображение второго (overlay) изображения под первое
        #image2 = image2.resize(image1.size)

        # Наложение второго изображения на первое
        #image1.paste(image2, (0, 0), image2.convert("RGBA").split()[3])  # Альфа-канал для прозрачности

        # Преобразуем результат в QPixmap для использования в PyQt6
        qimage = ImageQt.ImageQt(Avatar)  # Конвертируем в формат RGBA
        #data = image1.tobytes("raw", "RGBA")  # Получаем байты изображения
        #qimage = QImage(data, image1.width, image1.height, QImage.Format_RGBA)

        # Преобразуем QImage в QPixmap
        return QPixmap.fromImage(qimage)

        #self.label.setPixmap()





def excepthook(exc_type, exc_value, exc_tb):
  if not(exc_type==KeyboardInterrupt):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(tb)
    window.close()
  else:
    window.close()

UserEventType = QEvent.registerEventType()

def main():
    app = QApplication(sys.argv)

    if not(os.path.isfile(os.path.join("/tmp","discover_overlay_api.json"))):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Discover overlay is not running in VR API mode!")
        msg.setInformativeText("enable VR API support in the Discover overlay settings")
        msg.setWindowTitle("Foxlay VR-Overlay: Error")
        msg.exec()
        sys.exit()
    elif not(os.path.isfile(os.path.join(os.environ.get('XDG_RUNTIME_DIR'),"wayland-20"))):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("wlx-overlay-s composer not running!")
        msg.setInformativeText("Please launch VR to run this app")
        msg.setWindowTitle("Foxlay VR-Overlay: Error")
        msg.exec()
        sys.exit()
    else:
        os.environ["WAYLAND_DISPLAY"]="wayland-20"
        os.environ["GDK_BACKEND"]="wayland"

    window = TransparentWidget()


    window.show()
    sys.excepthook = excepthook
    
    sys.exit(app.exec())

    window.observer.join()
    window.observer.stop()


if __name__ == "__main__":
    main()
    