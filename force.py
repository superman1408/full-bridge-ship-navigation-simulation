import math

print("Welcome to the Ship Force Simulator!")
print("Please provide the following details about the ship geometry:")
print("--------------------------------------------------")
print("Note: Please enter the values in meters and percentage as required.")

name_of_ship = input("Enter the class of the ship: ")
print(f"The class of the ship is: {name_of_ship}")

length = float(input("Enter the length of the ship in meters: "))
print(f"The length of the ship is: {length} meters")

width = float(input("Enter the breadth of the ship in meters: "))
print(f"The breadth of the ship is: {width} meters")


draft = float(input("Enter the draft of the ship in meters: "))
print(f"The draft of the ship is: {draft} meters")

height = float(input("Enter the height of the ship in meters: "))
print(f"The height of the ship is: {height} meters")

displacement = float(input("Enter the displacement of the ship in tonnage: "))
print(f"The displacement of the ship is: {displacement} Ton")

loading_condition = input("Enter the percentage of loading condition (0-100): ")
loading_condition = float(loading_condition)
print(f"The loading condition of the ship is: {loading_condition}%")

print("---------------------------------------------------------")
print("Environment condition")


wind_speed = float(input("Enter the wind speed in meters/seconds: "))
print(f"Wind speed in system is: {wind_speed} m/s")

direction_wind = float(input("Enter the direction of wind blowing in degrees: "))
print(f"The direction of wind with respect to Carrier is: {direction_wind} degrees")


current_speed = float(input("Enter the current speed in meters/seconds: "))
print(f"Current speed in system is: {current_speed} m/s")

direction_current = float(input("Enter the direction of current flowing in degrees: "))
print(f"The direction of current with respect to Carrier is: {direction_current} degrees")



area_Aw = length * height
area_Ac = length * draft

air_density = 1.225 # Kg/meter^3
wind_coeffecient = 1.0 # Itteration
current_coeffecient = 1.0 # Itteration
seawater_density = 1025.0 # Kg/meter^3

print(f"Area of ship above seabed: {area_Aw} square meters")
print(f"Area of ship below seabed: {area_Ac} square meters")
print(f"Taking Air Density: {air_density} Kg/m^3, seawater density: {seawater_density} Kg/m^3 and Wind Coefficient is illustrated at factor {wind_coeffecient}.")


wind_force = (0.5 * air_density * wind_coeffecient * area_Aw * wind_speed**2) / 1000

current_force = (0.5 * seawater_density * current_coeffecient * area_Ac * current_speed**2) / 1000

total_force = wind_force + current_force

# Using Newton's second law to calculate the initial acceleration(Ay) of the vessel due to external forces (Wind & Current) acting on it..
Ay = total_force / (displacement * 1000)

print(f"Force acting on the carrier by wind: {wind_force} kN")
print(f"Force acting on the carrier by current: {current_force} kN")
print(f"Total force acting on the carrier: {total_force} kN")
print(f"Initial acceleration caused by acting force of {total_force} kN on the vessel is: {Ay} m/s^2")
