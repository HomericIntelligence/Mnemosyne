# Tolerant reader cross-version records — supporting evidence

## Breaking change with a deployed strict reader

A service published a discovery record with a new schema version. The new
record removed four required fields and added several fields that an older
deployed reader forbade. That reader was installed on worker hosts and could
not be rebuilt before the publisher rolled out. Calls failed with a missing
key error in one path and a strict validation error with ten findings in
another path.

The repair kept the predecessor field set at the original public path and
published the complete new record at a separate versioned path. Current
readers use the versioned path. An older strict reader keeps parsing the
path it already knows. A behavior test parses the predecessor projection
with a strict reader and the new record with the current reader.

## Decision value

A tolerant read model fixes additive-field failures in readers that can be
rebuilt. It cannot repair a reader already deployed with a strict model and
different required fields. In that condition, treat the public path as a
versioned interface: preserve the old shape at the old path and add a new
path for the new schema.
