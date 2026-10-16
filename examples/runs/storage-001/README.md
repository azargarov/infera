# Reviewed `storage-001` run

This reviewed synthetic run demonstrates a localized storage failure. The
agent observed a full disposable filesystem, a controlled `demo-api` write
failure with `errno=28`, and healthy root filesystem capacity. Its finding
scope identifies the affected filesystem explicitly and keeps ownership,
retention, and future growth as unknowns.

No files were deleted, logs truncated, filesystems remounted, or storage
resized. The run was validated structurally and by the storage scenario
evaluator.
