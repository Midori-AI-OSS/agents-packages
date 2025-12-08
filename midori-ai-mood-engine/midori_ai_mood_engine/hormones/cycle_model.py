"""Hormone cycle model with PyTorch-based simulation."""

import math

import torch

from torch import nn
from torch import Tensor

from datetime import datetime
from datetime import timedelta

from ..enums import StepType


class HormoneCycleModel(nn.Module):
    """PyTorch-based model to simulate hormone level trajectories across a 28-day cycle."""

    @classmethod
    def _build_phase_offsets(cls) -> dict[str, float]:
        """Build phase offsets dictionary one pair at a time."""
        offsets: dict[str, float] = {}
        offsets["gnrh"] = 0.0
        offsets["fsh"] = 0.2
        offsets["lh"] = 1.0
        offsets["estradiol"] = 0.8
        offsets["progesterone"] = 1.5
        offsets["inhibin_a"] = 1.5
        offsets["inhibin_b"] = 0.3
        offsets["activin"] = 0.3
        offsets["amh"] = -0.5
        offsets["prolactin"] = 0.0
        offsets["hcg"] = 2.0
        offsets["relaxin"] = 1.5
        offsets["testosterone"] = 0.2
        offsets["dhea"] = 0.2
        offsets["cortisol"] = 0.0
        offsets["adrenaline"] = 3.0
        offsets["norepinephrine"] = 2.8
        offsets["melatonin"] = 2.5
        offsets["oxytocin"] = 1.2
        offsets["serotonin"] = 0.4
        offsets["dopamine"] = 0.7
        offsets["gaba"] = 0.5
        offsets["endorphins"] = 1.0
        offsets["insulin"] = 0.3
        offsets["leptin"] = 1.3
        offsets["ghrelin"] = -0.5
        offsets["t3"] = 0.1
        offsets["t4"] = 0.1
        return offsets

    def __init__(self, cycle_start: datetime, step_type: StepType = StepType.DAY):
        """Initialize the hormone cycle model."""
        super(HormoneCycleModel, self).__init__()

        self.cycle_start: datetime = cycle_start
        self.step_type: StepType = step_type

        if step_type == StepType.PULSE:
            self.num_steps: int = 28 * 16
        elif step_type == StepType.FULL:
            self.num_steps: int = 28 * 24 * 60 * 2
        else:
            self.num_steps: int = 28

        self._init_reproductive_params()
        self._init_stress_params()
        self._init_mood_params()
        self._init_metabolism_params()

    def _init_reproductive_params(self) -> None:
        """Initialize reproductive hormone parameters."""
        self.gnrh_params: Tensor = nn.Parameter(torch.tensor([1.0, 0.5], dtype=torch.float32))
        self.fsh_params: Tensor = nn.Parameter(torch.tensor([3.0, 1.5], dtype=torch.float32))
        self.lh_params: Tensor = nn.Parameter(torch.tensor([2.5, 1.0], dtype=torch.float32))
        self.estradiol_params: Tensor = nn.Parameter(torch.tensor([100.0, 150.0], dtype=torch.float32))
        self.progesterone_params: Tensor = nn.Parameter(torch.tensor([1.0, 0.8], dtype=torch.float32))
        self.inhibin_a_params: Tensor = nn.Parameter(torch.tensor([10.0, 5.0], dtype=torch.float32))
        self.inhibin_b_params: Tensor = nn.Parameter(torch.tensor([8.0, 4.0], dtype=torch.float32))
        self.activin_params: Tensor = nn.Parameter(torch.tensor([5.0, 2.5], dtype=torch.float32))
        self.amh_params: Tensor = nn.Parameter(torch.tensor([2.0, 1.0], dtype=torch.float32))
        self.prolactin_params: Tensor = nn.Parameter(torch.tensor([10.0, 3.0], dtype=torch.float32))
        self.hcg_params: Tensor = nn.Parameter(torch.tensor([0.1, 0.05], dtype=torch.float32))
        self.relaxin_params: Tensor = nn.Parameter(torch.tensor([0.5, 0.3], dtype=torch.float32))
        self.testosterone_params: Tensor = nn.Parameter(torch.tensor([0.2, 0.1], dtype=torch.float32))
        self.dhea_params: Tensor = nn.Parameter(torch.tensor([0.3, 0.15], dtype=torch.float32))

    def _init_stress_params(self) -> None:
        """Initialize stress hormone parameters."""
        self.cortisol_params: Tensor = nn.Parameter(torch.tensor([5.0, 2.0], dtype=torch.float32))
        self.adrenaline_params: Tensor = nn.Parameter(torch.tensor([1.0, 0.9], dtype=torch.float32))
        self.norepinephrine_params: Tensor = nn.Parameter(torch.tensor([1.2, 0.8], dtype=torch.float32))

    def _init_mood_params(self) -> None:
        """Initialize mood hormone parameters."""
        self.melatonin_params: Tensor = nn.Parameter(torch.tensor([2.0, 1.8], dtype=torch.float32))
        self.oxytocin_params: Tensor = nn.Parameter(torch.tensor([3.0, 2.0], dtype=torch.float32))
        self.serotonin_params: Tensor = nn.Parameter(torch.tensor([10.0, 3.5], dtype=torch.float32))
        self.dopamine_params: Tensor = nn.Parameter(torch.tensor([6.0, 2.0], dtype=torch.float32))
        self.gaba_params: Tensor = nn.Parameter(torch.tensor([4.0, 1.5], dtype=torch.float32))
        self.endorphins_params: Tensor = nn.Parameter(torch.tensor([3.0, 1.2], dtype=torch.float32))

    def _init_metabolism_params(self) -> None:
        """Initialize metabolism hormone parameters."""
        self.insulin_params: Tensor = nn.Parameter(torch.tensor([8.0, 3.0], dtype=torch.float32))
        self.leptin_params: Tensor = nn.Parameter(torch.tensor([5.0, 2.0], dtype=torch.float32))
        self.ghrelin_params: Tensor = nn.Parameter(torch.tensor([4.0, 2.5], dtype=torch.float32))
        self.t3_params: Tensor = nn.Parameter(torch.tensor([1.5, 0.5], dtype=torch.float32))
        self.t4_params: Tensor = nn.Parameter(torch.tensor([7.0, 2.0], dtype=torch.float32))

    def _compute_step_index(self, current_time: datetime) -> int:
        """Compute the step index for the given datetime."""
        delta: timedelta = current_time - self.cycle_start

        if self.step_type == StepType.PULSE:
            total_minutes = delta.total_seconds() / 60.0
            pulse_index = int(total_minutes // 90)
            return pulse_index % self.num_steps
        elif self.step_type == StepType.FULL:
            total_half_minutes = delta.total_seconds() / 30.0
            half_min_index = int(total_half_minutes)
            return half_min_index % self.num_steps
        else:
            day_index = delta.days
            return day_index % self.num_steps

    def forward(self, step_index: int) -> dict[str, Tensor]:
        """Compute hormone levels for the given step index."""
        phase: float = float(step_index) / float(self.num_steps) * 2.0 * math.pi

        def compute_level(params: Tensor, offset: float = 0.0) -> Tensor:
            baseline: Tensor = params[0]
            amplitude: Tensor = params[1]
            angle: Tensor = torch.tensor(phase + offset, dtype=params.dtype)
            return baseline + amplitude * torch.sin(angle)

        offsets = self._build_phase_offsets()

        hormone_levels: dict[str, Tensor] = {}
        hormone_levels["GnRH"] = compute_level(self.gnrh_params, offsets["gnrh"])
        hormone_levels["FSH"] = compute_level(self.fsh_params, offsets["fsh"])
        hormone_levels["LH"] = compute_level(self.lh_params, offsets["lh"])
        hormone_levels["Estradiol"] = compute_level(self.estradiol_params, offsets["estradiol"])
        hormone_levels["Progesterone"] = compute_level(self.progesterone_params, offsets["progesterone"])
        hormone_levels["Inhibin_A"] = compute_level(self.inhibin_a_params, offsets["inhibin_a"])
        hormone_levels["Inhibin_B"] = compute_level(self.inhibin_b_params, offsets["inhibin_b"])
        hormone_levels["Activin"] = compute_level(self.activin_params, offsets["activin"])
        hormone_levels["AMH"] = compute_level(self.amh_params, offsets["amh"])
        hormone_levels["Prolactin"] = compute_level(self.prolactin_params, offsets["prolactin"])
        hormone_levels["hCG"] = compute_level(self.hcg_params, offsets["hcg"])
        hormone_levels["Relaxin"] = compute_level(self.relaxin_params, offsets["relaxin"])
        hormone_levels["Testosterone"] = compute_level(self.testosterone_params, offsets["testosterone"])
        hormone_levels["DHEA"] = compute_level(self.dhea_params, offsets["dhea"])
        hormone_levels["Cortisol"] = compute_level(self.cortisol_params, offsets["cortisol"])
        hormone_levels["Adrenaline"] = compute_level(self.adrenaline_params, offsets["adrenaline"])
        hormone_levels["Norepinephrine"] = compute_level(self.norepinephrine_params, offsets["norepinephrine"])
        hormone_levels["Melatonin"] = compute_level(self.melatonin_params, offsets["melatonin"])
        hormone_levels["Oxytocin"] = compute_level(self.oxytocin_params, offsets["oxytocin"])
        hormone_levels["Serotonin"] = compute_level(self.serotonin_params, offsets["serotonin"])
        hormone_levels["Dopamine"] = compute_level(self.dopamine_params, offsets["dopamine"])
        hormone_levels["GABA"] = compute_level(self.gaba_params, offsets["gaba"])
        hormone_levels["Endorphins"] = compute_level(self.endorphins_params, offsets["endorphins"])
        hormone_levels["Insulin"] = compute_level(self.insulin_params, offsets["insulin"])
        hormone_levels["Leptin"] = compute_level(self.leptin_params, offsets["leptin"])
        hormone_levels["Ghrelin"] = compute_level(self.ghrelin_params, offsets["ghrelin"])
        hormone_levels["T3"] = compute_level(self.t3_params, offsets["t3"])
        hormone_levels["T4"] = compute_level(self.t4_params, offsets["t4"])

        return hormone_levels

    def get_levels_at_datetime(self, current_time: datetime) -> dict[str, Tensor]:
        """Compute hormone levels for a given datetime."""
        step_index = self._compute_step_index(current_time)
        return self.forward(step_index)

    def get_mood_mods(self, step_index: int) -> dict[str, float]:
        """Compute mood modifiers from hormone levels."""
        levels = self.forward(step_index)

        lh = levels["LH"].item()
        estradiol = levels["Estradiol"].item()
        progesterone = levels["Progesterone"].item()
        testosterone = levels["Testosterone"].item()
        cortisol = levels["Cortisol"].item()
        melatonin = levels["Melatonin"].item()
        adrenaline = levels["Adrenaline"].item()
        serotonin = levels["Serotonin"].item()
        dopamine = levels["Dopamine"].item()
        oxytocin = levels["Oxytocin"].item()
        gaba = levels["GABA"].item()
        endorphins = levels["Endorphins"].item()

        energy_mod = (estradiol - 100.0) / 150.0 - (progesterone / 0.5) + (dopamine / 4.0) - (melatonin / 1.5) + (adrenaline / 2.0) + (testosterone / 0.3)
        irritability_mod = (cortisol - 5.0) / 2.0 - (serotonin / 15.0) + (adrenaline / 2.0) + (estradiol - 100.0) / 200.0 - (progesterone / 2.0) + (testosterone / 0.4)
        mood_swings_mod = (lh - 2.5) / 1.0 - (oxytocin / 5.0) + (estradiol - 100.0) / 180.0 + (cortisol - 5.0) / 8.0 - (progesterone / 1.5)
        happiness_mod = (dopamine / 12.0) + (serotonin / 20.0) + (oxytocin / 8.0) - (cortisol / 5.0) + (progesterone / 6.0) + (testosterone / 1.0) + (endorphins / 6.0) - 0.5
        anxiety_mod = (cortisol / 4.0) + (adrenaline / 2.0) - (gaba / 3.0) - (serotonin / 15.0) - (endorphins / 8.0)
        focus_mod = (dopamine / 8.0) - (cortisol / 10.0) + (testosterone / 0.5) - (melatonin / 3.0)
        libido_mod = (testosterone / 0.2) + (estradiol - 100.0) / 200.0 - (progesterone / 2.0) + (dopamine / 10.0)
        sleep_quality_mod = (melatonin / 2.0) + (gaba / 4.0) - (cortisol / 8.0) - (adrenaline / 3.0) + (serotonin / 20.0)

        energy_mod = max(energy_mod, 0)  # Energy cannot be negative as it represents physical/mental capacity

        mood_mods: dict[str, float] = {}
        mood_mods["energy"] = energy_mod
        mood_mods["irritability"] = irritability_mod
        mood_mods["mood_swings"] = mood_swings_mod
        mood_mods["happiness"] = happiness_mod
        mood_mods["anxiety"] = anxiety_mod
        mood_mods["focus"] = focus_mod
        mood_mods["libido"] = libido_mod
        mood_mods["sleep_quality"] = sleep_quality_mod

        return mood_mods

    def get_mood_at_datetime(self, current_time: datetime) -> dict[str, float]:
        """Compute mood modifiers for a given datetime."""
        step_index = self._compute_step_index(current_time)
        return self.get_mood_mods(step_index)

    def is_on_period(self, current_time: datetime) -> tuple[bool, float]:
        """Determine menstrual state based on current hormone levels."""
        levels = self.get_levels_at_datetime(current_time)

        estradiol = levels["Estradiol"].item()
        progesterone = levels["Progesterone"].item()
        fsh = levels["FSH"].item()

        is_period = estradiol < 60.0 and progesterone < 0.3 and fsh > 3.5
        intensity = max(0, min(1, (60.0 - estradiol) / 40.0)) if is_period else 0.0

        return is_period, intensity
