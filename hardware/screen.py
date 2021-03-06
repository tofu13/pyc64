from datetime import datetime

from .constants import *

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
# noinspection PyUnresolvedReferences


class Screen:
    def __init__(self, memory):
        self.memory = memory

        # Watchers
        self.memory.write_watchers.append((0x0400, 0x07E7, self.char_code))
        self.memory.write_watchers.append((0xD800, 0xDBE7, self.char_color))
        self.memory.write_watchers.append((0xD000, 0xD3FF, self.set_registers))
        self.memory.read_watchers.append((0xD000, 0xD3FF, self.get_registers))

        # Registers
        self.pointer_character_memory = 0x0000
        self.pointer_bitmap_memory = 0x0000
        self.pointer_screen_memory = 0x0000

        self.horizontal_raster_scroll = 0
        self.vertical_raster_scroll = 3
        self.full_screen_width = 1
        self.full_screen_height = 1
        self.screen_on = 0
        self.bitmap_mode = 0
        self.multicolor_mode = 0
        self.extended_background_mode = 0

        self.irq_raster_line = 0
        self.irq_raster_enabled = 1
        self.irq_sprite_background_collision_enabled = 1
        self.irq_sprite_sprite_collision_enabled = 1
        self.irq_status_register = 0

        self.border_color = 14
        self.background_color = 6
        self.extra_background_color_1 = 0
        self.extra_background_color_2 = 0
        self.extra_background_color_3 = 0

        self.transparent_color = pygame.color.Color(1, 254, 0)

        self.palette = [[c >> 16, (c >> 8) & 0xFF, c & 0xFF] for c in COLORS]
        self.background_pos_full = [41, 42]
        self.background_pos_small = [46, 47]
        self.extra_borders = (7, 4)

        self.buffer_size = (320, 200)

        self.display_size = (403, 284)

        #pygame.init()
        pygame.display.set_caption("Commodore 64")

        # Listen for keyboard events enly
        #pygame.event.set_blocked(None)
        #pygame.event.set_allowed([pygame.KEYDOWN, pygame.KEYUP, pygame.QUIT])

        # Display is the entire window drawn - visible area
        self.display = pygame.display.set_mode(self.display_size, flags=pygame.DOUBLEBUF)

        # Background is where video memory is draw onto (sprites can be outside)
        self.background = pygame.Surface(self.buffer_size)

        # Buffer is the actual memory buffer
        self.buffer = pygame.Surface(self.buffer_size)
        self.buffer.set_colorkey(self.transparent_color)

        self.font_cache = []
        self.cache_fonts()

        self.refresh()

    @property
    def current_raster_line(self):
        return int((datetime.now().microsecond % 20000) / 20000 * 312)

    def refresh(self, area=None):
        # Refresh entire display. Relatively slow unless update area is specified
        # buffer -> background -> display

        # Calc relative position of buffer on background. 3 pixel down by default (why?)
        buffer_pos = (self.horizontal_raster_scroll, self.vertical_raster_scroll - 3)

        background_pos = (
            self.background_pos_full[0] if self.full_screen_width else self.background_pos_small[0],
            self.background_pos_full[1] if self.full_screen_height else self.background_pos_small[1]
        )

        clipping_rect = (
            0 if self.full_screen_width else self.extra_borders[0],
            0 if self.full_screen_height else self.extra_borders[1],
            self.buffer_size[0] - (0 if self.full_screen_width else self.extra_borders[0] * 2),
            self.buffer_size[1] - (0 if self.full_screen_height else self.extra_borders[1] * 2),
        )

        # Clear display
        self.display.fill(PALETTE[self.border_color])
        # Clear background (need to?)
        self.background.fill(PALETTE[self.background_color])

        # Draw video buffer onto background
        # pygame.draw.rect(self.buffer, (0, 255, 0), self.buffer.get_rect(), width=1)
        self.background.blit(self.buffer, buffer_pos)

        # Draw centered background (with video buffer) centered on display
        # pygame.draw.rect(self.background, (0, 0, 255), self.background.get_rect(), width=1)
        self.display.blit(self.background, background_pos, clipping_rect)

        # Update
        if area:
            area.move_ip(buffer_pos)
            area.move_ip(background_pos)
            #pygame.draw.rect(self.display, (255, 0, 0), area, width=1)
            pygame.display.update(area) # Updates full screen????
            #pygame.display.flip()
            #print(area)
        else:
            pygame.display.flip()
            print("flip!")

    def dump(self):
        for attr in dir(self):
            if hasattr(self, attr):
                print("obj.%s = %s" % (attr, getattr(self, attr)))

    def cache_fonts(self):
        chargen = self.memory.get_chargen()  # Dirty trick to speed up things
        for i in range(512):
            matrix = chargen[i * 8:(i + 1) * 8]

            char_colors = []
            for color in PALETTE:
                font = pygame.Surface((8, 8))
                for r, row in enumerate(matrix):
                    for c, bit in enumerate(f"{row:08b}"):
                        font.set_at((c, r), color if bit == "1" else self.transparent_color)
                char_colors.append(font)
                font.set_colorkey(self.transparent_color)

            self.font_cache.append(char_colors)

    def char_code(self, address, value):
        self.set_char(address, value, color=self.memory[address - 0x0400 + 0xD800] & 0x0F)

    def char_color(self, address, value):
        self.set_char(address - 0xD800 + 0x400, self.memory[address - 0xD800 + 0x400], color=value & 0x0F)

    def set_char(self, address, value, color, screen_update=True):
        char = self.font_cache[value][color & 0x0F]
        coords = ((address - 0x400) % 40) * 8, int((address - 0x400) / 40) * 8

        # pygame.draw.rect(self.buffer, PALETTE[self.background_color], pygame.rect.Rect(coords, (8, 8)))
        char_rect = char.get_rect().move(coords)
        self.buffer.fill(PALETTE[self.background_color], char_rect)
        self.buffer.blit(char, coords)
        if screen_update:
            self.refresh(char_rect)

    def refresh_buffer(self):
        self.buffer.fill(PALETTE[self.background_color])
        for i in range(0x0400, 0x7E8):
            self.set_char(i, self.memory[i], self.memory[i - 0x400 + 0xD800], screen_update=False)
        self.refresh()

    def get_registers(self, address, value):
        if address == 0xD011:
            """
            Bits #0-#2: Vertical raster scroll.
            Bit #3: Screen height; 0 = 24 rows; 1 = 25 rows.
            Bit #4: 0 = Screen off, complete screen is covered by border; 1 = Screen on, normal screen contents are visible.
            Bit #5: 0 = Text mode; 1 = Bitmap mode.
            Bit #6: 1 = Extended background mode on.
            Bit #7: Read: Current raster line (bit #8).

            Write: Raster line to generate interrupt at (bit #8).
        
            Default: $1B, %00011011.
            """
            return \
                self.vertical_raster_scroll |\
                self.full_screen_height << 3 |\
                0 << 4 |\
                0 << 5 |\
                (self.current_raster_line > 0xFF) << 7

        elif address == 0xD016:
            """
            Screen control register #2. Bits:
            Bits #0-#2: Horizontal raster scroll.
            Bit #3: Screen width; 0 = 38 columns; 1 = 40 columns.
            Bit #4: 1 = Multicolor mode on.
            Default: $C8, %11001000.
            """
            return \
                self.horizontal_raster_scroll |\
                self.full_screen_width << 3 |\
                0 << 4 |\
                0b11000000


        elif address == 0xD012:
            return self.current_raster_line & 0xFF

        if address == 0xD019:
            return 1  # Temporary, to be completed
        return value

    def set_registers(self, address, value):
        #print ("Set VIC register", address, value)
        if address == 0xD011:
            self.vertical_raster_scroll = value & 0b00000111
            self.full_screen_height = (value & 0b00001000) >> 3
            self.screen_on = (value & 0b00010000) >> 4
            self.bitmap_mode = (value & 0b00100000) >> 5
            self.extended_background_mode = (value & 0b01000000) >> 6
            # Set bit 8 of irq_raster_line
            self.irq_raster_line = (value & 0b10000000) << 1 | (self.irq_raster_line & 0xFF)

            self.refresh()

        elif address == 0xD016:
            self.horizontal_raster_scroll = value & 0b00000111
            self.full_screen_width = (value & 0b00001000) >> 3
            self.multicolor_mode = (value & 0b00010000) >> 4

            self.refresh()

        elif address == 0xD01A:
            self.irq_raster_enabled = value & 0b0001
            self.irq_sprite_background_collision_enabled = value & 0b0010
            self.irq_sprite_sprite_collision_enabled = value & 0b0100

        elif address == 0xD020:
            self.border_color = value & 0x0F
            self.refresh()

        elif address == 0xD021:
            self.background_color = value & 0x0F
            self.refresh_buffer()
            return


if __name__ == '__main__':
    s = Screen()
    pass

