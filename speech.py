# -*- coding: utf-8 -*-
"""SAPI 语音朗读"""
import subprocess
from config import SPEAK_VBS


def speak(text):
    """朗读文本(通过 wscript + SAPI.SpVoice)"""
    if not text:
        return
    try:
        safe = text.replace('"', '""').replace("\n", " ")
        with open(SPEAK_VBS, "w", encoding="utf-8") as f:
            f.write('Set v = CreateObject("SAPI.SpVoice")\n')
            f.write("On Error Resume Next\n")
            f.write("v.Rate = -2\n")
            f.write('v.Speak "' + safe + '"\n')
        subprocess.Popen(
            ["wscript.exe", "//B", "//Nologo", SPEAK_VBS],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
