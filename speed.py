import math


# ==========================================================
# SHIP NAVIGATION CALCULATIONS
# STW | SOG | CURRENT | COG
# ==========================================================

def velocity_vector(speed, direction):
    """
    Nautical convention:
        0   = North
        90  = East
        180 = South
        270 = West

    Speed unit: knots
    Direction unit: degrees

    Returns:
        East component (knots), North component (knots)
    """

    rad = math.radians(direction)

    east = speed * math.sin(rad)
    north = speed * math.cos(rad)

    return east, north


def vector_to_speed_direction(east, north):
    """Convert East/North velocity components into speed and direction."""

    speed = math.hypot(east, north)

    if speed < 1e-10:
        direction = None
    else:
        direction = math.degrees(
            math.atan2(east, north)
        ) % 360

    return speed, direction


# ==========================================================
# MODE 1:
# STW + HEADING + CURRENT
# CALCULATE SOG + COG
# ==========================================================

def calculate_from_current(
    stw,
    ship_heading,
    current_speed,
    current_direction
):

    # Ship movement relative to water
    ship_east, ship_north = velocity_vector(
        stw, ship_heading
    )

    # Current movement relative to ground
    current_east, current_north = velocity_vector(
        current_speed, current_direction
    )

    # Ground velocity components
    ground_east = ship_east + current_east
    ground_north = ship_north + current_north

    # Calculate SOG and COG
    sog, cog = vector_to_speed_direction(
        ground_east, ground_north
    )

    return {
        "STW": stw,
        "Heading": ship_heading,
        "Current Speed": current_speed,
        "Current Direction": current_direction,
        "SOG": sog,
        "COG": cog,
        "Ship East": ship_east,
        "Ship North": ship_north,
        "Current East": current_east,
        "Current North": current_north,
        "Ground East": ground_east,
        "Ground North": ground_north
    }


# ==========================================================
# MODE 2:
# STW + HEADING + SOG + COG
# CALCULATE CURRENT SPEED + CURRENT DIRECTION
# ==========================================================

def calculate_from_ground(
    stw,
    ship_heading,
    sog,
    cog
):

    # Ship movement relative to water
    ship_east, ship_north = velocity_vector(
        stw, ship_heading
    )

    # Ground movement
    ground_east, ground_north = velocity_vector(
        sog, cog
    )

    # Current = Ground velocity - Ship velocity
    current_east = ground_east - ship_east
    current_north = ground_north - ship_north

    # Calculate current speed and direction
    current_speed, current_direction = vector_to_speed_direction(
        current_east, current_north
    )

    return {
        "STW": stw,
        "Heading": ship_heading,
        "SOG": sog,
        "COG": cog,
        "Current Speed": current_speed,
        "Current Direction": current_direction,
        "Ship East": ship_east,
        "Ship North": ship_north,
        "Ground East": ground_east,
        "Ground North": ground_north,
        "Current East": current_east,
        "Current North": current_north
    }


# ==========================================================
# DISPLAY RESULTS WITH UNITS
# ==========================================================

def display_results(data):

    print("\n" + "=" * 60)
    print("              SHIP NAVIGATION DATA")
    print("=" * 60)

    # Speed and direction values
    display_units = {
        "STW": "kn",
        "Heading": "deg",
        "SOG": "kn",
        "COG": "deg",
        "Current Speed": "kn",
        "Current Direction": "deg"
    }

    for key in display_units:

        value = data.get(key)
        unit = display_units[key]

        if value is None:
            print(f"{key:22}: N/A")
        else:
            print(f"{key:22}: {value:.2f} {unit}")

    print("-" * 60)

    # Velocity components
    component_units = "kn"

    for key in [
        "Ship East",
        "Ship North",
        "Current East",
        "Current North",
        "Ground East",
        "Ground North"
    ]:

        value = data.get(key)

        if value is not None:
            print(
                f"{key:22}: "
                f"{value:.3f} {component_units}"
            )

    print("=" * 60)


# ==========================================================
# EXAMPLE 1:
# STW + HEADING + CURRENT
# ==========================================================

result1 = calculate_from_current(
    stw=0.0,
    ship_heading=45.0,
    current_speed=3.0,
    current_direction=90.0
)

print("\nEXAMPLE 1: CALCULATE SOG AND COG")
display_results(result1)


# ==========================================================
# EXAMPLE 2:
# STW + HEADING + SOG + COG
# CALCULATE CURRENT SPEED + CURRENT DIRECTION
# ==========================================================

result2 = calculate_from_ground(
    stw=5.0,
    ship_heading=45.0,
    sog=4.0,
    cog=60.0
)

print("\nEXAMPLE 2: CALCULATE CURRENT")
display_results(result2)