import os
import weaviate

client = weaviate.Client(
    url=os.getenv("WEAVIATE_URL"),
    auth_client_secret=weaviate.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY"))
)

# Create schema
schema = {
    "class": "LegalDocument",
    "vectorizer": "text2vec-openai",
    "properties": [
        {"name": "text", "dataType": ["text"]},
        {"name": "source", "dataType": ["text"]},
        {"name": "section", "dataType": ["text"]}
    ]
}

client.schema.create_class(schema)