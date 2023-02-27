#!/usr/bin/env python

import time
from colorsys import hsv_to_rgb
from PIL import Image, ImageDraw, ImageFont
from ST7789 import ST7789
import pygame
import eyed3
import pathlib
import RPi.GPIO as GPIO
import random
import logging
import atexit

logging.basicConfig(level="INFO")

FONT = ImageFont.truetype('/home/pi/pirate-audio/examples/abel-regular.ttf', 32)
BUTTONS = [5, 6,16 ,24]
LABELS = ['A', 'B', 'X', 'Y']

global PAUSED
PAUSED = False

global TIMEOUT
TIMEOUT = 0

global songs
songs = []

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

st7789 = ST7789(
    rotation=90,
    port=0,
    cs=1,
    dc=9,
    backlight=13,
    spi_speed_hz = 80 * 1000 * 1000
)

def exit_handler():
    image = Image.new("RGB", (240, 240), (0,0,0))
    ImageDraw.Draw(image)
    st7789.display(image)
    st7789.set_backlight(0)

atexit.register(exit_handler)

def load_library():
    music_library = pathlib.Path("/home/pi/pirate-audio/examples/Music")
    album_library = {}
    for item in music_library.rglob("*mp3"):
        item_array = str(item).split('/')
        album = item_array[7].replace(" ", "_")
        if not album_library.get(album):
            album_library[album] = []
        album_library[album].append(str(item))
    return album_library

def write_text_to_screen(text_array):
    image = Image.new("RGB", (240, 240), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    height = 0
    for text_item in text_array:
        draw.text(
            (0,height),
            text_item,
            (255,255,255),
            font=FONT
        )
        height += 50
    st7789.display(image)

def is_playing():
    global PAUSED
    if pygame.mixer.music.get_busy() or PAUSED:
        return True
    return False

def handle_button(pin):
    global PAUSED
    global TIMEOUT
    global songs
    if GPIO.input(13) == 0:
        st7789.set_backlight(1)
        TIMEOUT = 0
        return
    TIMEOUT = 0
    label = LABELS[BUTTONS.index(pin)]
    if label == 'X':
        pygame.mixer.music.stop()
        songs = []
    if label == 'A':
        if PAUSED:
            pygame.mixer.music.unpause()
            PAUSED = False
        else:
            pygame.mixer.music.pause()
            PAUSED = True
    if label == 'B':
        pygame.mixer.music.set_volume(pygame.mixer.music.get_volume() - 0.05)
    if label == 'Y':
        pygame.mixer.music.set_volume(pygame.mixer.music.get_volume() + 0.05)
    print(f"Button pressed {label}")
    time.sleep(0.5)

for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=100)

def load_albums_from_library(library):
    albums = [album_name for album_name in library.keys()]
    random.shuffle(albums)
    return albums

library = load_library()
albums = load_albums_from_library(library)
write_text_to_screen([])

pygame.mixer.init()
pygame.mixer.music.set_volume(0.2)

while True:
    if not songs:
        album = albums[0]
        songs = library[album]
        songs.sort(key=lambda x: x.split('/')[-1])
    song = songs[0]
    pygame.mixer.music.load(song)
    pygame.mixer.music.play()
    while is_playing():
        TIMEOUT += 1
        if TIMEOUT > 10:
            st7789.set_backlight(0)
        audiofile = eyed3.load(song)
        song_metadata_array = [
            audiofile.tag.artist,
            audiofile.tag.title,
            audiofile.tag.album
        ]
        write_text_to_screen(song_metadata_array)
        time.sleep(1)
    if len(songs) > 0:
        songs.pop(0)
    if len(songs) == 0:
        albums.pop(0)
    if len(albums) == 0:
        library = load_library()
        load_albums_from_library(library)
