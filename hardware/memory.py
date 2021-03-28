from multiprocessing import Array

class Memory:
    read_watchers = []
    write_watchers = []
    roms = {}
    chargen, loram, hiram = None, None, None

    def init(self):
        # Default processor port (HIRAM, LORAM, CHARGEN = 1)
        self[1] = 7

    def __getitem__(self, address):
        # print(f"Memory read at {item}: {value}")
        if 0xA000 <= address <= 0xBFFF:
            if self.hiram and self.loram:
                return self.roms['basic'][address - 0xA000]
        elif 0xE000 <= address <= 0xFFFF:
            if self.hiram:
                return self.roms['kernal'][address - 0xE000]
        elif 0xD000 <= address <= 0xDFFF:
            if not self.chargen and (not self.hiram and not self.loram):
                return self.roms['chargen'][address - 0xD000]
            else:
                for start, end, callback in self.read_watchers:
                    if start <= address <= end:
                        return callback(address, super().__getitem__(address))

        return super().__getitem__(address)

    def __setitem__(self, address, value):
        if value < 0 or value > 255:
            raise ValueError(f"Trying to write to memory a value ({value}) out of range (0-255).")

        # Hard coded processor port at $01
        if address == 1:
            self.chargen, self.loram, self.hiram = map(bool,map(int, f"{value & 0x7:03b}"))

        for start, end, callback in self.write_watchers:
            if start <= address <= end:
                callback(address, value)
                break
        # print(f"Memory write at {key}: {value}")
        super().__setitem__(address, value)

    def __str__(self, start=0x100, end=None):
        if end is None:
            end = start + 0x0100
        return "\n".join(
            [f"{i:04X}: {super(__class__, self).__getitem__(slice(i, i + 16))}" for i in range(start, end, 16)]
        )

    def get_chargen(self):

        return self.roms['chargen']

    def loop(self, bus):
        while True:
            msg = bus.recv()
            print("memory receive", msg)
            if msg.startswith("R"):
                address = int(msg[2:])
                bus.send(f"R:{address}:{self[address]}")
            elif msg.startswith("W"):
                address, value = map(int, msg[2:].split(":"))
                self[address] = value
                bus.send(f"W:{address}:{value}")
            elif msg == "QUIT":
                break



class BytearrayMemory(Memory, bytearray):
    pass

class CTypesMemory:
    read_watchers = []
    write_watchers = []
    roms = {}
    contents = Array('B',65536)

    def __getitem__(self, address):
        # print(f"Memory read at {item}: {value}")
        value = self.contents[address]
        chargen, loram, hiram = map(int, f"{self.contents[1] & 0x7:03b}")

        if 0xA000 <= address <= 0xBFFF:
            if hiram and loram:
                return self.roms['basic'][address - 0xA000]
        elif 0xE000 <= address <= 0xFFFF:
            if hiram:
                return self.roms['kernal'][address - 0xE000]
        elif 0xD000 <= address <= 0xDFFF:
            if not chargen and (not hiram and not loram):
                return self.roms['chargen'][address - 0xD000]
            elif chargen:
                for start, end, callback in self.read_watchers:
                    if start <= address <= end:
                        return callback(address, value)
        return value

    def __setitem__(self, address, value):
        if value < 0 or value > 255:
            raise ValueError(f"Trying to write to memory a value ({value}) out of range (0-255).")
        for start, end, callback in self.write_watchers:
            if start <= address <= end:
                callback(address, value)
                break
        # print(f"Memory write at {key}: {value}")
        self.contents[address] = value

if __name__ == '__main__':
    m = BytearrayMemory(65536)
    print(m)
