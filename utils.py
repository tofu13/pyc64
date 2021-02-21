import subprocess
from os.path import basename


def compile(compiler, filename):
    subprocess.run(f"{compiler['path']} {compiler['options']} -o {filename} {filename}.asm".split())
