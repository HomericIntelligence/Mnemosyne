# ProjectHephaestus Priority-Aging Plan Notes

## Session status

- Date: 2026-07-20
- Artifact: review-refined implementation plan
- Verification: unverified
- Production code changed: no
- Tests or lint executed against ProjectHephaestus: no
- CI observed: no

## Proposed implementation surface

- Coordinator drain method: `hephaestus/automation/pipeline/coordinator.py`,
  `Coordinator._drain_implementation()`.
- Existing lifecycle state: `WorkItem.payload` in
  `hephaestus/automation/pipeline/work_item.py`.
- Dependency ordering: `order_for_implementation()` in
  `hephaestus/automation/pipeline/admission.py`.
- Overlap serialization: `_select_non_overlapping()` in the same admission module.
- Coordinator tests: `tests/unit/automation/pipeline/test_coordinator.py`.
- Selector tests: `tests/unit/automation/pipeline/test_admission.py`.

## Proposed parameters

```python
_FILE_OVERLAP_DEFERRALS_KEY = "file_overlap_deferrals"
_FILE_OVERLAP_WARNING_THRESHOLD = 10
```

Counts `1..10` remain `INFO`; every count greater than `10` is `WARNING`.
The counter resets only after `_admit(item)` succeeds and the item is about to run.

## Proposed tests

1. `test_file_overlap_aging_dispatches_starved_issue`
   - Use identical planned paths for issues `#21` and `#22`.
   - Mock only `_fetch_planned_files()` so the production overlap selector runs.
   - Fill the repository worker cap in round one. Issue `#21` wins selection but
     cannot dispatch; issue `#22` is overlap-deferred and gains age.
   - Open capacity in round two and assert `#22` dispatches before `#21`.
2. `test_file_overlap_warning_threshold`
   - Parameterize starting counts `9`, `10`, and `11`.
   - Assert resulting counts `10`, `11`, and `12` log at `INFO`, `WARNING`, and
     `WARNING`.
3. Strengthen `test_topo_order_and_overlap_reuse`
   - Give highly aged issue `#21` a dependency on `#22`.
   - Assert the overlap selector still receives `[22, 21]`.

## Proposed verification commands

```bash
uv run pytest tests/unit/automation/pipeline/test_coordinator.py \
  -k "file_overlap_aging_dispatches_starved_issue or file_overlap_warning_threshold or topo_order_and_overlap_reuse" -v

uv run pytest tests/unit/automation/pipeline/test_coordinator.py \
  tests/unit/automation/pipeline/test_admission.py \
  -k "topo_order_and_overlap_reuse or select_non_overlapping_defers_second_of_overlapping_pair" -v

uv run pytest tests/unit/automation/pipeline -q

uv run ruff check hephaestus/automation/pipeline/coordinator.py \
  tests/unit/automation/pipeline/test_coordinator.py
```

## Review corrections captured

- Put the regression, boundary, and dependency tests before production changes
  and require a focused failing run.
- Exercise the real overlap selector by mocking only planned-file retrieval.
- Define strict `count > 10` warning semantics and cover `10`, `11`, and `12`.
- Document the coordinator-local rollback and absence of persistent migration.
