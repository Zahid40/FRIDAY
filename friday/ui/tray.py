import threading
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

class SystemTrayIcon:
    def __init__(self, on_show_callback, on_quit_callback):
        self.on_show = on_show_callback
        self.on_quit = on_quit_callback
        self.icon = None
        self.thread = None

    def create_icon_image(self):
        # Dynamically draw a glowing purple circle icon
        width = 16
        height = 16
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw base glowing circle
        dc.ellipse([1, 1, 14, 14], fill=(124, 110, 250, 255), outline=(160, 80, 255, 255), width=1)
        
        # Draw gloss specular spot
        dc.ellipse([4, 4, 7, 7], fill=(255, 255, 255, 220))
        return image

    def run(self):
        # Create tray menu
        menu = pystray.Menu(
            item('Show FRIDAY', self.on_show, default=True),
            item('Quit', self.on_quit)
        )
        self.icon = pystray.Icon("friday_tray", self.create_icon_image(), "FRIDAY", menu)
        
        # Execute the tray run loop in a daemon thread so it doesn't block the main GUI thread
        self.thread = threading.Thread(target=self.icon.run, daemon=True)
        self.thread.start()

    def stop(self):
        if self.icon:
            self.icon.stop()
