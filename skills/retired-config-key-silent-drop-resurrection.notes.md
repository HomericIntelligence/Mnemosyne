# Notes: Retired Config Keys: Silent Drop and New-File Resurrection

Supporting evidence for
[retired-config-key-silent-drop-resurrection](retired-config-key-silent-drop-resurrection.md).
The main entry holds the rule; this file holds detail and measurements.

## Source case

A change registered a new group of serving configuration files. The files were
adapted from an older sibling recipe and kept its qualification-gate line. An
earlier merged change had removed that gate from the configuration model and
replaced it with a pre-validation step that drops three retired keys.

The model stayed strict for every other unknown key, so an author could not see
the defect by reading the model: the three names were in the drop set. The
documented reason for the drop step was compatibility with older files and
older release artifacts.

## Measurements

| Fact | Value |
| --- | --- |
| Configuration files in the tree | 35 |
| Files naming a retired key | 13 |
| Files naming a retired key that predated the change | 0 |
| Retired keys in the drop set | 3 |
| Tests failing from the dead attribute in the first hosted run | 1 |
| Lint gate failing on the same line | 1 (type checker) |
| Test-tier configuration failing from the same run | 1 (unrelated new-module classification defect, repaired in the same head) |

The "0 pre-existing" row is the decisive measurement. The drop step was written
for legacy files, yet none remained. That showed the keys arrived by
copy-forward, not by any live compatibility need.

## Discovery commands

```bash
# The drop step and its key set.
rg -n '_RETIRED|mode="before"' src/
rg -n 'retired.*drop' src/

# Which files carry a retired key.
rg -l '<retired_key>' config/

# Prove the loader drops rather than rejects.
python3 -c 'from pkg.config import load_file; m = load_file("config/new.yaml"); print(m)'
```

## What the type checker caught

The guard test read the property through the model object. Because the field is
absent from the model, the access is an unresolved attribute at the type level.
The lint gate reported:

```
error[unresolved-attribute]: Object of type `ConfigModel` has no attribute `<retired_key>`
```

The test itself failed at runtime with an attribute error. Both signals point to
the same defect: the key was retired. Running the type checker on the changed
files locally before push would have shown the dead reference without a hosted
run.

## Repair

1. Delete the retired key from each new file. This changes no runtime behavior,
   because the loader dropped the value before the model read it.
2. Change the guard to compare the retired-key set against the raw document.
   Import the set from the configuration module so that a future retirement
   joins the guard automatically.
3. Keep the intended property through the explicit fields that the runtime
   enforces: a disabled/enabled flag, a minimum replica count of zero, a maximum
   of one, and null capacity and service-objective fields.
4. Update the file comment so that it describes the enforcing mechanism instead
   of the removed setting.

## Related checks that surfaced at the same time

A new configuration file can also miss a field that an installer or a client
publishes a per-model table for. In the source case, both new model files
omitted a context-length field, and the installer's published table did not list
the new models. A test compared the table against every configuration file and
failed in both directions. When you add configuration files, check every
consumer table that must stay in step. Two of those tables existed here:
generated schemas, and an operator-facing limits map.

This is a companion hazard, not part of the main rule. It shares the trigger
(add configuration files) and a different failure mode (a missing consumer row
instead of a retired key).

## Privacy screen

The source case is described without repository, organization, product, path,
or issue identifiers. The counts are kept because they carry the decision: zero
pre-existing files made the copy-forward origin visible. Commands use
placeholder names for the configuration module and file.