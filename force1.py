
import math


def calculate_environmental_forces(
    length,
    breadth,
    draft,
    height,
    displacement_tonnes,
    ship_heading,
    ship_vx,
    ship_vy,
    wind_speed,
    wind_direction,
    current_speed,
    current_direction,
):
    """
    Simplified environmental-force model.

    Angles: 0 = North, 90 = East.
    Directions indicate where wind/current are flowing TO.
    Velocities are in m/s.
    Forces are returned in newtons (N).
    """

    # Basic validation
    if min(length, breadth, draft, height, displacement_tonnes) <= 0:
        raise ValueError("Ship dimensions and displacement must be positive.")

    if min(wind_speed, current_speed) < 0:
        raise ValueError("Environmental speeds cannot be negative.")

    # Densities in kg/m^3
    air_density = 1.225
    seawater_density = 1025.0

    # Initial placeholder drag coefficients.
    # Replace these with vessel-specific validated values later.
    wind_cd_long = 1.0
    wind_cd_lateral = 1.0
    current_cd_long = 1.0
    current_cd_lateral = 1.0

    # Projected areas (m^2)
    wind_front_area = breadth * height
    wind_side_area = length * height

    current_front_area = breadth * draft
    current_side_area = length * draft

    # Ship heading unit vectors:
    # Forward direction and starboard (right) direction.
    heading_rad = math.radians(ship_heading)

    forward_x = math.sin(heading_rad)
    forward_y = -math.cos(heading_rad)

    right_x = math.cos(heading_rad)
    right_y = math.sin(heading_rad)

    def environmental_force(
        density,
        speed,
        direction,
        front_area,
        side_area,
        cd_long,
        cd_lateral,
    ):
        # Convert environmental velocity into world x/y components.
        direction_rad = math.radians(direction)

        env_vx = speed * math.sin(direction_rad)
        env_vy = -speed * math.cos(direction_rad)

        # Relative flow velocity: environment minus ship velocity.
        rel_vx = env_vx - ship_vx
        rel_vy = env_vy - ship_vy

        # Resolve relative velocity into ship coordinates.
        u_long = rel_vx * forward_x + rel_vy * forward_y
        u_lateral = rel_vx * right_x + rel_vy * right_y

        # Signed drag forces (N).
        # Squared speed preserves the direction of the relative flow.
        force_long = (
            0.5 * density * cd_long * front_area
            * u_long * abs(u_long)
        )

        force_lateral = (
            0.5 * density * cd_lateral * side_area
            * u_lateral * abs(u_lateral)
        )

        # Convert body-coordinate forces back to world x/y.
        force_x = (
            force_long * forward_x
            + force_lateral * right_x
        )

        force_y = (
            force_long * forward_y
            + force_lateral * right_y
        )

        return force_x, force_y

    # Calculate wind force.
    wind_fx, wind_fy = environmental_force(
        air_density,
        wind_speed,
        wind_direction,
        wind_front_area,
        wind_side_area,
        wind_cd_long,
        wind_cd_lateral,
    )

    # Calculate current force.
    current_fx, current_fy = environmental_force(
        seawater_density,
        current_speed,
        current_direction,
        current_front_area,
        current_side_area,
        current_cd_long,
        current_cd_lateral,
    )

    # Add forces as vectors, not as magnitudes.
    total_fx = wind_fx + current_fx
    total_fy = wind_fy + current_fy

    total_force = math.hypot(total_fx, total_fy)

    # Actual vessel mass in kilograms.
    mass_kg = displacement_tonnes * 1000.0

    # Newton's second law: acceleration = force / mass.
    acceleration_x = total_fx / mass_kg
    acceleration_y = total_fy / mass_kg

    return {
        "wind_fx_N": wind_fx,
        "wind_fy_N": wind_fy,
        "current_fx_N": current_fx,
        "current_fy_N": current_fy,
        "total_fx_N": total_fx,
        "total_fy_N": total_fy,
        "total_force_N": total_force,
        "acceleration_x": acceleration_x,
        "acceleration_y": acceleration_y,
    }


# -------------------------------
# Example test
# -------------------------------

result = calculate_environmental_forces(
    length=295.0,
    breadth=46.0,
    draft=12.0,
    height=30.0,
    displacement_tonnes=100000.0,
    ship_heading=90.0,
    ship_vx=0.0,
    ship_vy=0.0,
    wind_speed=10.0,
    wind_direction=90.0,
    current_speed=1.0,
    current_direction=90.0,
)

print("\n--- Environmental Force Results ---")

for key, value in result.items():
    print(f"{key}: {value:.3f}")
