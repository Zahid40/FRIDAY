import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# Configure global logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s"
)

# Import Friday GUI elements
from gui.pill_widget import PillWidget
from gui.voice_thread import VoiceThread
from gui.tray import SystemTrayIcon

class HotkeySignaler(QObject):
    """
    Listens for a global hotkey event in a background thread 
    and signals the main thread to toggle widget visibility safely.
    """
    hotkey_pressed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        try:
            import keyboard
            keyboard.add_hotkey("ctrl+space", self.trigger_signal)
            logging.info("Registered global toggle hotkey: Ctrl + Space")
        except Exception as e:
            logging.error(f"Failed to register keyboard hotkey: {e}")
        
    def trigger_signal(self):
        self.hotkey_pressed.emit()

def main():
    app = QApplication(sys.argv)
    
    # Prevent application from closing when the window is hidden/minimized
    app.setQuitOnLastWindowClosed(False)
    
    # Create the floating pill widget
    pill = PillWidget()
    pill.show()
    
    # Initialize the Voice Pipeline QThread
    voice_thread = VoiceThread()
    
    # Connect signals from the voice processing thread to UI slots
    voice_thread.state_changed.connect(pill.update_state)
    voice_thread.text_updated.connect(pill.update_text)
    voice_thread.time_elapsed.connect(pill.update_time)
    
    # Start the Voice Thread loop
    voice_thread.start()
    
    # Define Tray callbacks
    def show_friday():
        # Ensure UI modification runs on Qt main loop thread
        QTimer.singleShot(0, lambda: (
            pill.show(),
            pill.activateWindow(),
            pill.raise_(),
            pill.update_state("idle")
        ))
        
    def quit_friday():
        logging.info("Shutting down Friday assistant...")
        tray.stop()
        voice_thread.stop_thread()
        app.quit()
        sys.exit(0)
        
    # Start System Tray icon
    tray = SystemTrayIcon(on_show_callback=show_friday, on_quit_callback=quit_friday)
    tray.run()
    
    # Setup global hotkey handler
    hotkey_signaler = HotkeySignaler()
    
    def toggle_visibility():
        if pill.isVisible():
            pill.hide()
        else:
            pill.show()
            pill.activateWindow()
            pill.raise_()
            pill.update_state("idle")
            
    hotkey_signaler.hotkey_pressed.connect(toggle_visibility)
    
    # Start Qt event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
