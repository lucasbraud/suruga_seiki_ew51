"""Example usage of the EW-51 SDK client.

This script demonstrates basic usage of the SDK to control the motion system.
Make sure the daemon is running before executing this script:

    suruga-ew51-daemon --mock

Then run this example:

    python examples/example_client.py
"""

import asyncio
import logging

from suruga_seiki_ew51.sdk import EW51Client
from suruga_seiki_ew51.models import AxisId, MovementRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Main example demonstrating SDK usage."""
    logger.info("=" * 60)
    logger.info("Suruga Seiki EW-51 SDK Example")
    logger.info("=" * 60)

    # Create client and connect
    async with EW51Client("http://localhost:8000") as client:
        # Check health
        logger.info("\n1. Checking daemon health...")
        health = await client.health()
        logger.info(f"   Status: {health.status}")
        logger.info(f"   Version: {health.version}")
        logger.info(f"   Mock mode: {health.is_mock}")

        # Get initial status
        logger.info("\n2. Getting initial station status...")
        status = await client.get_status()
        logger.info(f"   Daemon state: {status.station.daemon_state}")
        logger.info(f"   Connection: {status.station.connection_established}")
        logger.info(f"   Left stage axes: {len(status.station.left_stage.axes)}")
        logger.info(f"   Right stage axes: {len(status.station.right_stage.axes)}")

        # Enable servo for X1 axis
        logger.info("\n3. Enabling servo for X1 axis...")
        servo_responses = await client.enable_servo([AxisId.X1])
        for resp in servo_responses:
            logger.info(f"   {resp.axis.name}: {'enabled' if resp.enabled else 'disabled'}")

        # Get initial position
        logger.info("\n4. Getting initial position of X1...")
        initial_pos = await client.get_position(AxisId.X1)
        logger.info(f"   Initial position: {initial_pos:.2f} µm")

        # Move axis to 1000 µm
        logger.info("\n5. Moving X1 to 1000 µm...")
        move_response = await client.move_axis(
            axis=AxisId.X1,
            target=1000.0,
            relative=False,
            wait=True,
        )
        logger.info(f"   Status: {move_response.status}")
        logger.info(f"   Final position: {move_response.current_position:.2f} µm")

        # Move relative -200 µm
        logger.info("\n6. Moving X1 relative -200 µm...")
        move_response = await client.move_axis(
            axis=AxisId.X1,
            target=-200.0,
            relative=True,
            wait=True,
        )
        logger.info(f"   Status: {move_response.status}")
        logger.info(f"   Final position: {move_response.current_position:.2f} µm")

        # Get all positions
        logger.info("\n7. Getting all axis positions...")
        all_positions = await client.get_all_positions()
        logger.info(f"   Total axes: {len(all_positions.positions)}")
        for pos in all_positions.positions[:3]:  # Show first 3
            logger.info(f"   {pos.axis.name}: {pos.value:.2f} µm")

        # Multi-axis movement example
        logger.info("\n8. Moving multiple axes simultaneously...")
        movements = [
            MovementRequest(axis=AxisId.X1, target=500.0, relative=False, wait=True),
            MovementRequest(axis=AxisId.Y1, target=300.0, relative=False, wait=True),
        ]
        # First enable servo for Y1
        await client.enable_servo([AxisId.Y1])

        multi_response = await client.move_multiple_axes(movements, wait=True)
        logger.info(f"   Overall status: {multi_response.overall_status}")
        for move_resp in multi_response.movements:
            logger.info(
                f"   {move_resp.axis.name}: {move_resp.status} "
                f"(position: {move_resp.current_position:.2f} µm)"
            )

        # Get axis status
        logger.info("\n9. Getting detailed status for X1...")
        axis_status = await client.get_axis_status(AxisId.X1)
        logger.info(f"   Position: {axis_status.position:.2f} µm")
        logger.info(f"   Servo enabled: {axis_status.servo_enabled}")
        logger.info(f"   Is moving: {axis_status.is_moving}")
        logger.info(f"   Is homed: {axis_status.is_homed}")

        # Disable servos
        logger.info("\n10. Disabling servos...")
        servo_responses = await client.disable_servo([AxisId.X1, AxisId.Y1])
        for resp in servo_responses:
            logger.info(
                f"   {resp.axis.name}: {'enabled' if resp.enabled else 'disabled'}"
            )

        logger.info("\n" + "=" * 60)
        logger.info("Example completed successfully!")
        logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
