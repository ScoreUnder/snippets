from math import sin, cos, pi

def main():
    parts = 7
    coords = [(sin(n * pi * 2 / parts), cos(n * pi * 2 / parts)) for n in range(parts)]
    # Include white coord:
    # coords += [(0, 0)]
    mul = 0.7

    for i, (x, y) in enumerate(coords):
        print(f"PulseAttractor(vec3(0.5, {mul*x:f}, {mul*y:f}), 16.0, 3.0)", end='')
        if i == len(coords) - 1:
            print("")
        else:
            print(",")

main()
