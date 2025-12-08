"""Tests for the self-retraining system."""

import pytest

from midori_ai_mood_engine import FeedbackSample
from midori_ai_mood_engine import MoodTrainer
from midori_ai_mood_engine.hormones import HormoneCycleModel
from midori_ai_mood_engine import StepType

import pytz

from datetime import datetime


@pytest.fixture
def model():
    """Create a test hormone model."""
    tz = pytz.timezone("America/Los_Angeles")
    cycle_start = datetime(2008, 4, 15, 0, 0, 0, tzinfo=tz)
    return HormoneCycleModel(cycle_start=cycle_start, step_type=StepType.DAY)


@pytest.fixture
def trainer(model):
    """Create a test trainer."""
    return MoodTrainer(model=model, learning_rate=0.001)


def test_trainer_initialization(trainer):
    """Test trainer initialization."""
    assert trainer is not None
    assert trainer.model is not None
    assert trainer.optimizer is not None


def test_add_feedback(trainer):
    """Test adding feedback samples."""
    trainer.add_feedback(predicted={"happiness": 0.7, "energy": 0.5}, actual={"happiness": 0.5, "energy": 0.6})
    assert trainer.get_buffer_size() == 1


def test_clear_buffer(trainer):
    """Test clearing the feedback buffer."""
    trainer.add_feedback(predicted={"happiness": 0.7}, actual={"happiness": 0.5})
    trainer.add_feedback(predicted={"happiness": 0.6}, actual={"happiness": 0.4})
    count = trainer.clear_buffer()
    assert count == 2
    assert trainer.get_buffer_size() == 0


def test_retrain_no_data(trainer):
    """Test retraining with no data."""
    result = trainer.retrain()
    assert result["status"] == "no_data"


def test_retrain_with_data(trainer):
    """Test retraining with feedback data."""
    for i in range(5):
        trainer.add_feedback(predicted={"happiness": 0.5 + i * 0.1}, actual={"happiness": 0.4 + i * 0.1})
    result = trainer.retrain(epochs=3)
    assert result["status"] == "completed"
    assert result["samples"] == 5
    assert result["epochs"] == 3
    assert "final_loss" in result


def test_feedback_sample_creation():
    """Test creating FeedbackSample objects."""
    sample = FeedbackSample(predicted={"happiness": 0.7, "energy": 0.5}, actual={"happiness": 0.5, "energy": 0.6}, context={"time": "morning"})
    assert sample.predicted["happiness"] == 0.7
    assert sample.actual["happiness"] == 0.5
    assert sample.context["time"] == "morning"


def test_retrain_clears_buffer(trainer):
    """Test that retraining clears the buffer."""
    trainer.add_feedback(predicted={"happiness": 0.7}, actual={"happiness": 0.5})
    trainer.retrain()
    assert trainer.get_buffer_size() == 0
