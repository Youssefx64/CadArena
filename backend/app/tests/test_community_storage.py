from pathlib import Path

from app.services import community_storage


def _use_temp_db(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "community.db"
    monkeypatch.setattr(community_storage, "workspace_db_path", lambda: db_path)
    community_storage.init_community_db()


def test_community_question_answer_and_vote_flow(monkeypatch, tmp_path):
    _use_temp_db(monkeypatch, tmp_path)

    question = community_storage.create_question(
        title="How should I coordinate slab openings near beams?",
        body=(
            "I have a residential slab with several services crossing near a primary beam. "
            "What should be checked before freezing the architectural opening positions?"
        ),
        tags=["slabs", "Coordination", "beams"],
        discipline="structural",
        author_id=None,
        author_name="Site Engineer",
    )

    assert question["answer_count"] == 0
    assert question["tags"] == ["slabs", "coordination", "beams"]

    answer = community_storage.add_answer(
        question_id=question["id"],
        body=(
            "Check the structural drawings first, keep openings away from high shear zones, "
            "and coordinate sleeve dimensions with MEP before issuing the final layout."
        ),
        author_id="user-1",
        author_name="Structural Lead",
    )

    assert answer is not None
    assert answer["score"] == 0

    voted_question = community_storage.vote_question(question_id=question["id"], direction=1)
    voted_answer = community_storage.vote_answer(answer_id=answer["id"], direction=1)

    assert voted_question["score"] == 1
    assert voted_answer["score"] == 1

    detail = community_storage.get_question(question_id=question["id"], increment_views=True)

    assert detail["question"]["view_count"] == 1
    assert detail["question"]["answer_count"] == 1
    assert detail["answers"][0]["author_name"] == "Structural Lead"

    filtered = community_storage.list_questions(query="slab openings", tag="coordination", discipline="structural")

    assert [item["id"] for item in filtered] == [question["id"]]
