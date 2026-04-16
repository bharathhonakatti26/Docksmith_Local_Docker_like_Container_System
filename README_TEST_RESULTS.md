# Docksmith Requirement Test Results

Reference: `requirement.txt`

## Summary

- Automated suite run: 14 test cases
- Passed: 13
- Failed: 1
- Retest of failed case (`run_invalid_no_cmd`): Passed
- Practical final status for executed cases: **14/14 passed**

## Detailed results

1. `build_cold_valid` -> PASS
2. `build_warm_cache_hit` -> PASS
3. `images_list_valid` -> PASS
4. `run_default_valid` -> PASS
5. `run_env_override_valid` -> PASS
6. `run_cmd_override_valid` -> PASS
7. `build_invalid_missing_docksmithfile` -> PASS
8. `build_invalid_unsupported_instruction` -> PASS
9. `build_invalid_missing_base` -> PASS
10. `run_invalid_missing_image` -> PASS
11. `run_invalid_no_cmd` -> PASS on retest
12. `rmi_invalid_missing_image` -> PASS
13. `rmi_valid_existing_image` -> PASS
14. `runtime_isolation_write_check` -> PASS (heuristic host file check)

## Important notes from execution

- Build output now logs all 6 Docksmithfile steps (`FROM`, `WORKDIR`, `ENV`, `COPY`, `RUN`, `CMD`).
- Friendly CLI errors are shown for invalid inputs (no traceback): build/run/rmi/pull.
- Base image strict check works: missing `FROM` base fails clearly.
- Unsupported instructions fail with line numbers.

## What you still need to do (to fully match requirement.txt)

The command tests above passed, but there are remaining requirement-level gaps to address in implementation:

1. `COPY` glob support (`*`, `**`) is required by spec and should be explicitly implemented and tested.
2. `CMD` must enforce JSON array form (`CMD ["exec","arg"]`), not shell-split text.
3. Manifest layer entries should include required metadata fields (`size`, `createdBy`) per requirement format.
4. Manifest digest should be computed from canonical manifest with `digest=""` before final write (exact spec behavior).
5. `WORKDIR` creation semantics should follow spec exactly (create in temp FS before next layer-producing instruction if missing).
6. Hard isolation requirement should fail closed when isolation primitives are unavailable (current fallback behavior is weaker than strict requirement intent).
7. Reproducibility and timestamp constraints should be re-verified for repeated cache-hit rebuilds (including preserved `created` semantics).

## Recommended next actions

1. Implement missing `COPY` glob behavior and add tests for wildcard paths.
2. Enforce strict JSON-array parsing for `CMD` and add invalid-format test.
3. Update manifest writer to include required layer metadata and canonical digest process.
4. Add a strict-isolation mode for demo/pass-fail evaluation.
5. Re-run this suite and record updated results.
