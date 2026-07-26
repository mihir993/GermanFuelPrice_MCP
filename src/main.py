from core.tools.server import mcp
import logging

logger = logging.getLogger(__name__)

# Import tools so they get registered via decorators
import core.tools.fuel_price_mcp

# Entry point to run the server
if __name__ == "__main__":
    logger.info("Starting German fuel price MCP.")
    mcp.run()