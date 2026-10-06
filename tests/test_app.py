from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


TEST_ACTIVITY = "Basketball Team"
TEST_EMAIL = "test-student@example.com"


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_root_redirects_to_static_homepage(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activity = activities[TEST_ACTIVITY]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[TEST_ACTIVITY] == expected_activity
    assert {"description", "schedule", "max_participants", "participants"} <= set(
        response.json()[TEST_ACTIVITY]
    )


def test_signup_adds_participant(client):
    # Arrange
    participants = activities[TEST_ACTIVITY]["participants"]
    assert TEST_EMAIL not in participants

    # Act
    response = client.post(
        f"/activities/{TEST_ACTIVITY}/signup", params={"email": TEST_EMAIL}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {TEST_EMAIL} for {TEST_ACTIVITY}"
    }
    assert TEST_EMAIL in participants


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    participants = activities[TEST_ACTIVITY]["participants"]
    participants.append(TEST_EMAIL)

    # Act
    response = client.post(
        f"/activities/{TEST_ACTIVITY}/signup", params={"email": TEST_EMAIL}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert participants.count(TEST_EMAIL) == 1


def test_signup_rejects_unknown_activity(client):
    # Arrange
    unknown_activity = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{unknown_activity}/signup", params={"email": TEST_EMAIL}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_requires_email(client):
    # Arrange
    url = f"/activities/{TEST_ACTIVITY}/signup"

    # Act
    response = client.post(url)

    # Assert
    assert response.status_code == 422


def test_remove_signup_removes_participant(client):
    # Arrange
    participants = activities[TEST_ACTIVITY]["participants"]
    participants.append(TEST_EMAIL)

    # Act
    response = client.delete(
        f"/activities/{TEST_ACTIVITY}/signup", params={"email": TEST_EMAIL}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Removed {TEST_EMAIL} from {TEST_ACTIVITY}"
    }
    assert TEST_EMAIL not in participants


def test_remove_signup_rejects_unregistered_participant(client):
    # Arrange
    participants = activities[TEST_ACTIVITY]["participants"]
    assert TEST_EMAIL not in participants

    # Act
    response = client.delete(
        f"/activities/{TEST_ACTIVITY}/signup", params={"email": TEST_EMAIL}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_remove_signup_rejects_unknown_activity(client):
    # Arrange
    unknown_activity = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{unknown_activity}/signup", params={"email": TEST_EMAIL}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"