# Session Notes: Sealed Artifact Public Hardlink Projection

## Provenance

- Source: an anonymized shared-cluster artifact-service design review on 2026-11-18.
- The source session inspected filesystem metadata and the implementation of artifact verification, sealed manifests, image admission, and public path policy. It did not implement or roll out the design.
- The operator could change source file modes but could not change the administrative root or source directories. A full public mirror exceeded available capacity. The selected design therefore used permanent public hardlinks for immutable data and independent copies for single-link metadata.
- On the inspected target, the administrative and public roots were on the same device. The exact hardlink operation still requires a probe on the execution node. A second cluster was not inspected and remains a deployment prerequisite.

## Evidence That Changed the Design

1. **The strict link check covered the large image, not only its receipt.** The initial assumption was that only small JSON records required one link. Source inspection showed that the same single-link helper verified both the image and receipt. The design therefore needed a narrowly scoped data-image exception while receipts and probes remained strict.
2. **The sealed manifest included ctime in file identity.** Adding a hardlink or changing a mode changed ctime without changing bytes. Leaving the manifest stale could make every later verification rehash the full artifact. Publication and rollback therefore both need a metadata-only identity refresh that preserves the content-derived ID.
3. **A hardlink shares source metadata.** Sealing after publication, or repairing a public mode in place, would modify the administrative source too. Source data files must reach their final read-only mode before the first public link. Source directories remain unchanged.
4. **Metadata records and data files need different publication rules.** The large immutable data can have an approved second link. Manifests, receipts, sidecars, and pointers that require one link must be copied and independently sealed.
5. **A closed ancestor defeats symbolic links.** A public symlink cannot grant traversal through the administrative root. The public tree must contain real directory entries for the approved artifacts, and every public ancestor must be traversable by the intended reader.

## Corpus Disposition

Created a new entry rather than amending an existing one. Existing guidance covers independent-copy relocation, recovery of a frozen hardlink tree, single-link anchor publication, ancestor permission checks, and sealed-directory addition. None covered the combined permanent-public-projection intent with a bounded verifier exception and ctime-bound manifest refresh. One open change reviewed during discovery addressed adding one new artifact to a sealed directory by copy; its copy-based workflow and different trigger were not expanded into this lesson.

## Verification Boundary

This is design-reviewed guidance, not an operational verification claim. No public artifact was published, no production permission changed, and no verifier implementation changed in the source session. Before reuse, test the exact filesystem hardlink primitive, ordinary-user traversal, content and link-count verification, ctime refresh, idempotent publication, and rollback on a disposable artifact.
