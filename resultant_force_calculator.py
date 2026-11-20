
import math

def resultant_force(forces):
    """
    forces = [(name, magnitude, angle_degrees), ...]
    Angle: counter-clockwise from positive X axis.
    """

    total_fx = 0.0
    total_fy = 0.0

    print("\nINDIVIDUAL FORCE COMPONENTS")
    print("-" * 55)

    for name, magnitude, angle in forces:
        radians = math.radians(angle)

        fx = magnitude * math.cos(radians)
        fy = magnitude * math.sin(radians)

        total_fx += fx
        total_fy += fy

        print(f"{name}:")
        print(f"  Force = {magnitude:.3f} N")
        print(f"  Fx    = {fx:.3f} N")
        print(f"  Fy    = {fy:.3f} N")

    resultant = math.hypot(total_fx, total_fy)
    direction = math.degrees(math.atan2(total_fy, total_fx))
    direction = direction % 360

    print("\nRESULTANT FORCE")
    print("-" * 55)
    print(f"Total Fx = {total_fx:.3f} N")
    print(f"Total Fy = {total_fy:.3f} N")
    print(f"Resultant magnitude = {resultant:.3f} N")
    print(f"Resultant direction = {direction:.3f} degrees")

    return resultant, direction


def main():
    forces = []

    count = int(input("Enter the number of forces: "))

    for i in range(count):
        print(f"\nForce {i + 1}")
        name = input("Force name: ")
        magnitude = float(input("Magnitude in N: "))
        angle = float(input("Direction angle in degrees: "))

        if magnitude < 0:
            raise ValueError("Force magnitude must not be negative.")

        forces.append((name, magnitude, angle))

    resultant_force(forces)


if __name__ == "__main__":
    main()
