from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


AZURE_ENDPOINT = (
    "https://fleetaid-resource.services.ai.azure.com/api/projects/fleetaid"
)

AGENT_NAME = "JanSathi"
AGENT_VERSION = "6"


project_client = AIProjectClient(
    endpoint=AZURE_ENDPOINT,
    credential=DefaultAzureCredential(),
)

openai_client = project_client.get_openai_client()


def ask_jansathi(message: str):

    response = openai_client.responses.create(
        input=[
            {
                "role": "user",
                "content": message,
            }
        ],
        extra_body={
            "agent_reference": {
                "name": AGENT_NAME,
                "version": AGENT_VERSION,
                "type": "agent_reference",
            }
        },
    )

    return response.output_text