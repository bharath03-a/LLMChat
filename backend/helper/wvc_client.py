import os
import weaviate
import weaviate.classes.config as wvc
from weaviate.classes.init import Auth
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


weaviate_url = os.environ.get("WEAVIATE_URL")
weaviate_api_key = os.environ.get("WEAVIATE_API_KEY")

if not weaviate_url or not weaviate_api_key:
    logger.error("WEAVIATE_URL or WEAVIATE_API_KEY environment variable is not set.")
    raise ValueError("Missing WEAVIATE_URL or WEAVIATE_API_KEY.")

try:
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
    )
    logger.info("Successfully connected to Weaviate Cloud.")
except Exception as e:
    logger.error(f"Failed to connect to Weaviate Cloud: {e}")
    raise

try:
    collection = client.collections.create(
        name="LegalDocument",
        properties=[
            wvc.Property(name="text", data_type=wvc.DataType.TEXT),
            wvc.Property(name="source", data_type=wvc.DataType.TEXT),
            wvc.Property(name="section", data_type=wvc.DataType.TEXT)
        ],
        vectorizer_config=wvc.Configure.Vectorizer.text2vec_openai(),
        generative_config=wvc.Configure.Generative.openai()
    )
    logger.info("Collection 'LegalDocument' created successfully.")
except Exception as e:
    logger.error(f"Failed to create collection: {e}")
finally:
    logger.info("Closing client connection.")
    client.close()