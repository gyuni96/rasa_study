import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[logging.FileHandler("action_server.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)