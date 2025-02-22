from pydantic import BaseModel
from typing import List
import httpx

class Setting(BaseModel):
    label: str
    type: str
    required: bool
    default: str

class TrackerPayload(BaseModel):
    channel_id: str
    return_url: str
    settings: List[Setting]


async def check_repo(payload: TrackerPayload):
    site = next((s.default for s in payload.settings if s.label == "repo_name"), None)

    try:
        latest_forks = set()
        async with httpx.AsyncClient() as client:
            GITHUB_API_URL = f"https://api.github.com/repos/{site}/forks"
            response = await client.get(GITHUB_API_URL, timeout=10)
            if response.status_code == 200:
                forks = response.json()
                new_forks = []
                for fork in forks:
                    fork_id = fork["id"]
                    if fork_id not in latest_forks:
                        latest_forks.add(fork_id)
                        new_forks.append({
                            "forked_by": fork["owner"]["login"],
                            "repo_name": fork["name"],
                            "forked_at": fork["created_at"],
                            "fork_url": fork["html_url"]
                        })

                message = "New forks detected:\n"
                for fork in new_forks:
                    message += (
                        f"🔄Repo: {fork['repo_name']}\n"
                        f"Forked by: {fork['forked_by']}\n"
                        f"Forked at: {fork['forked_at']}\n"
                        f"🎉URL: {fork['fork_url']}\n\n"
                    )

                # data follows telex webhook format. Your integration must call the return_url using this format
                data = {
                    "event_name": "Fork Tracker",
                    "message": message,
                    "status": "success",
                    "username": "Repo Monitor",
                }
                async with httpx.AsyncClient() as client:
                    await client.post(payload.return_url, json=data)
                return {"message": "Fork check completed", "new_forks": message}
            return f"{GITHUB_API_URL} is down (status {response.status_code})"
    except Exception as e:
        return f"{GITHUB_API_URL} check failed: {str(e)}"
    