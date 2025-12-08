"""Self-retraining system for the mood engine."""

import torch

from torch import nn
from torch import optim

from dataclasses import dataclass
from typing import Any


@dataclass
class FeedbackSample:
    """A single feedback sample for training."""
    predicted: dict[str, float]
    actual: dict[str, float]
    context: dict[str, Any] | None = None


class MoodTrainer:
    """Trainer for self-retraining the mood engine."""

    DEFAULT_REGULARIZATION_COEFFICIENT = 0.0001

    def __init__(self, model: nn.Module, learning_rate: float = 0.001, regularization_coefficient: float | None = None):
        """Initialize the trainer with a model."""
        self.model = model
        self.learning_rate = learning_rate
        self.regularization_coefficient = regularization_coefficient if regularization_coefficient is not None else self.DEFAULT_REGULARIZATION_COEFFICIENT
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        self.loss_fn = nn.MSELoss()
        self.feedback_buffer: list[FeedbackSample] = []

    def add_feedback(self, predicted: dict[str, float], actual: dict[str, float], context: dict[str, Any] | None = None) -> None:
        """Add a feedback sample to the buffer."""
        sample = FeedbackSample(predicted=predicted, actual=actual, context=context)
        self.feedback_buffer.append(sample)

    def retrain(self, feedback_data: list[FeedbackSample] | None = None, epochs: int = 10) -> dict[str, float]:
        """Retrain the model with collected feedback."""
        if feedback_data is not None:
            self.feedback_buffer.extend(feedback_data)

        if len(self.feedback_buffer) < 1:
            return {"status": "no_data", "samples": 0, "final_loss": 0.0}

        samples = self.feedback_buffer
        self.feedback_buffer = []

        total_loss = 0.0
        for epoch in range(epochs):
            epoch_loss = 0.0
            for sample in samples:
                self.optimizer.zero_grad()

                predicted_values = list(sample.predicted.values())
                actual_values = list(sample.actual.values())

                predicted_tensor = torch.tensor(predicted_values, dtype=torch.float32, requires_grad=True)
                actual_tensor = torch.tensor(actual_values, dtype=torch.float32)

                loss = self.loss_fn(predicted_tensor, actual_tensor)

                param_sum = sum(p.sum() for p in self.model.parameters())
                regularization = param_sum * self.regularization_coefficient * loss.detach()
                total_loss_with_reg = loss + regularization

                total_loss_with_reg.backward()
                self.optimizer.step()

                epoch_loss += loss.item()

            total_loss = epoch_loss / len(samples)

        return {"status": "completed", "samples": len(samples), "epochs": epochs, "final_loss": total_loss}

    def clear_buffer(self) -> int:
        """Clear the feedback buffer and return the number of cleared samples."""
        count = len(self.feedback_buffer)
        self.feedback_buffer = []
        return count

    def get_buffer_size(self) -> int:
        """Get the current size of the feedback buffer."""
        return len(self.feedback_buffer)


def create_trainer_for_model(model: nn.Module, learning_rate: float = 0.001) -> MoodTrainer:
    """Create a trainer for the given model."""
    return MoodTrainer(model=model, learning_rate=learning_rate)
