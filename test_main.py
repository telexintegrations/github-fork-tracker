import pytest, os
from fastapi.testclient import TestClient
from main import app
from github_tracker import TrackerPayload, Setting
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create a test client for the FastAPI app
client = TestClient(app)

# Test data
TEST_REPO_NAME = os.getenv("REPO_NAME")
TEST_SETTINGS = [
    Setting(label="repo_name", type="text", required=True, default=TEST_REPO_NAME),
]
TEST_PAYLOAD = TrackerPayload(
    channel_id = os.getenv("CHANNEL_ID"),
    return_url = os.getenv("RETURN_URL"),
    settings = TEST_SETTINGS,
)

# Test for the /integration.json endpoint
def test_get_integration_json():
    response = client.get("/integration.json")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["descriptions"]["app_name"] == "GitHub Fork Event Tracker"
    assert data["data"]["tick_url"].endswith("/tick")


# Test for the /tick endpoint
@pytest.mark.asyncio
async def test_tick_endpoint():
    # Mock the check_repo function to avoid making actual API calls
    async def mock_check_repo(payload: TrackerPayload):
        return {"message": "Fork check completed", "new_forks": "Test fork details"}

    # Replace the actual check_repo function with the mock
    from github_tracker import check_repo
    original_check_repo = check_repo
    check_repo = mock_check_repo

    # Make a POST request to the /tick endpoint
    response = client.post("/tick", json=TEST_PAYLOAD.dict())
    assert response.status_code == 200
    assert response.json() == {"message": "Task added to background tasks"}

    # Restore the original check_repo function
    check_repo = original_check_repo
