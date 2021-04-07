import pickle
import asyncio
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'


class Machine:
    def __init__(self, memory, cpu, screen, roms, ciaA):

        self.memory = memory
        self.cpu = cpu
        self.screen = screen
        self.roms = roms
        self.ciaA = ciaA

        self.memory.roms = self.roms.contents
        self.memory.init()

        self.cpu.memory = self.memory

        self.screen.memory = self.memory
        self.screen.init()

        self.ciaA.memory = self.memory
        self.ciaA.init()

    def run(self, address):
        loop = asyncio.get_event_loop()
        event_queue = asyncio.Queue()
        ciaA_IRQ = loop.create_task(self.ciaA.loop(event_queue), name="ciaA")
        cpu_loop = loop.create_task(self.cpu.run(event_queue, address), name="cpu")

        try:
            loop.run_until_complete(cpu_loop)
        except KeyboardInterrupt:
            cpu_loop.cancel()
        ciaA_IRQ.cancel()

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'rb') as f:
            machine = cls()
            machine.cpu.A = pickle.load(f)
            machine.cpu.X = pickle.load(f)
            machine.cpu.Y = pickle.load(f)
            machine.cpu.PC = pickle.load(f)
            machine.cpu.SP = pickle.load(f)
            machine.cpu.F = pickle.load(f)
            machine.cpu.memory = pickle.load(f)
        return machine

    def restore(self, filename):
        with open(filename, 'rb') as f:
            self.cpu.A = pickle.load(f)
            self.cpu.X = pickle.load(f)
            self.cpu.Y = pickle.load(f)
            self.cpu.PC = pickle.load(f)
            self.cpu.SP = pickle.load(f)
            self.cpu.F = pickle.load(f)
            memory = pickle.load(f)
            self.cpu.memory = memory
            self.screen.memory = memory
            self.ciaA.memory = memory

    def save(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.cpu.A, f)
            pickle.dump(self.cpu.X, f)
            pickle.dump(self.cpu.Y, f)
            pickle.dump(self.cpu.PC, f)
            pickle.dump(self.cpu.SP, f)
            pickle.dump(self.cpu.F, f)
            pickle.dump(self.memory, f)

    def load(self, filename, base, format_cbm=False):
        with open(filename, 'rb') as f:
            if format_cbm:
                # First two bytes are base address for loading into memory (cbm file format, little endian)
                l, h = f.read(2)
                base = h << 8 | l
            data = f.read()
        for i, b in enumerate(data):
            self.memory[base + i] = b
        print(f"Loaded {len(data)} bytes starting at ${base:04X}")
        return base
