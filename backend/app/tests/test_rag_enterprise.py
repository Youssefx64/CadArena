import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.core.auth import get_current_user
from app.routers.archchat import _direct_reply, _is_greeting, _session_dep

client = TestClient(app)

@pytest.fixture
def mock_rag_response():
    return {
        "answer": "This is a mock architectural guidance.",
        "sources": [
            {"id": "doc1", "text": "Building code section 4.2", "score": 0.95}
        ]
    }

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "test_user"
    user.name = "Tester"
    return user

@pytest.fixture
def mock_session():
    session = AsyncMock()
    return session

def create_mock_thread():
    thread = MagicMock()
    thread.id = "test_thread"
    thread.title = "Test Thread"
    thread.created_at = None
    thread.updated_at = None
    thread.last_message_at = None
    return thread


@pytest.mark.parametrize(
    "message",
    ["السلام عليكم", "السلام عليكم ورحمة الله وبركاته", "مرحبا كيف حالك", "hello", "hi there"],
)
def test_archchat_recognizes_standalone_greetings(message):
    assert _is_greeting(message) is True
    assert _direct_reply(message, has_project_files=False)


def test_archchat_requires_project_file_for_engineering_questions():
    assert "أحتاج ملف المشروع" in _direct_reply("ما نوع السلم؟", has_project_files=False)
    assert _direct_reply("What stair type is shown?", has_project_files=True) is None

@patch("httpx.AsyncClient.post")
def test_archchat_send_message_success(mock_post, mock_rag_response, mock_user, mock_session):
    resp = AsyncMock()
    resp.status_code = 200
    resp.json = MagicMock(return_value=mock_rag_response)
    resp.raise_for_status = MagicMock()
    mock_post.return_value = resp

    thread = create_mock_thread()
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[_session_dep] = lambda: mock_session
    
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = thread
    exec_result.scalar_one.return_value = 1
    mock_session.execute.return_value = exec_result

    try:
        thread_id = "test_thread"
        
        with patch("app.routers.archchat.ArchChatMessage") as mock_msg_class:
            user_msg = MagicMock()
            user_msg.id = "u1"
            user_msg.role = "user"
            user_msg.content = "..."
            user_msg.created_at = None
            
            assistant_msg = MagicMock()
            assistant_msg.id = "a1"
            assistant_msg.role = "assistant"
            assistant_msg.content = "This is a mock architectural guidance."
            assistant_msg.created_at = None
            assistant_msg.rag_sources = mock_rag_response["sources"]
            
            mock_msg_class.side_effect = [user_msg, assistant_msg]
            
            resp_api = client.post(
                f"/api/v1/archchat/threads/{thread_id}/messages",
                json={"content": "What are the rules for stairs?", "has_project_files": True}
            )
            
            assert resp_api.status_code == 200
            data = resp_api.json()
            assert data["assistant_message"]["content"] == "This is a mock architectural guidance."
    finally:
        app.dependency_overrides.clear()

@patch("httpx.AsyncClient.post")
def test_archchat_rag_failure_handling(mock_post, mock_user, mock_session):
    mock_post.side_effect = Exception("RAG service down")

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[_session_dep] = lambda: mock_session
    
    thread = create_mock_thread()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = thread
    exec_result.scalar_one.return_value = 1
    mock_session.execute.return_value = exec_result

    try:
        thread_id = "test_thread"
        
        resp = client.post(
            f"/api/v1/archchat/threads/{thread_id}/messages",
            json={"content": "Should fail", "has_project_files": True}
        )
        
        assert resp.status_code == 502
    finally:
        app.dependency_overrides.clear()
