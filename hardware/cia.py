from .constants import *
import time

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame

class CIAA:
    memory = None
    pipe = None
    keyboard_row = 0
    keyboard_col = 0

    def init(self):
        self.memory.read_watchers.append((0xDC00, 0xDCFF, self.get_registers))
        self.memory.write_watchers.append((0xDC00, 0xDCFF, self.set_registers))

    def loop(self, memory):
        while True:
            self.pipe.send("IRQ")
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.mod & pygame.KMOD_LSHIFT:
                        selector = 1
                    elif event.mod & pygame.KMOD_LALT:
                        selector = 2
                    else:
                        selector = 0
                    key = KEYTABLE.get(event.key)
                    if key:
                        key = key[selector]
                    if key:
                        # Inject char into keyboard buffer
                        #memory[0x277 + memory[0xC6]] = key
                        # Update counter
                        #memory[0xC6] += 1

                        row, col = KEYSCAN.get(event.key, [8,8])
                        self.keyboard_row = 0xFF - 2 ** row
                        self.keyboard_col = 0xFF - 2 ** col


                elif event.type == pygame.KEYUP:
                    self.memory[0xDC01] = 0xFF #No key pressed


            time.sleep(.2)


    def get_registers(self, address, value):
        #print("read ciaA", address)
        if address == 0xDC01:
            if self.memory[0xDC00] == self.keyboard_row:
                return self.keyboard_col
            else:
                return 0xFF
        else:
            return value

        return value

    def set_registers(self, address, value):
        #print("write ciaA", address, value)
        self.memory.contents[address] = value


class CIAB:
    memory = None

    def init(self):
        self.memory.read_watchers.append((0xDD00, 0xDDFF, self.get_registers))
        self.memory.write_watchers.append((0xDD00, 0xDDFF, self.set_registers))

    def loop(self, memory):
        while True:
            time.sleep(1)


    def get_registers(self, address, value):
        #print("read ciaA", address)
        return value
    def set_registers(self, address, value):
        #print("write ciaA", address, value)
        pass
