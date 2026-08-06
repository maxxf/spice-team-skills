# Generated — do not edit

These client configs are a published snapshot. The authoritative copies live in HQ at
`companies/spice/skills/campaign-plan/clients/`, and `client_config.py` prefers those when
an HQ checkout is present.

They are shipped here because teammates install the skill from this plugin and have no HQ
checkout — without the snapshot, a client that exists in HQ simply does not exist for them.

To change a client: edit it in HQ (or re-run `provision.py`), then run

    python3 references/publish_configs.py

and commit the result. Editing a file in this directory by hand will be overwritten by the
next publish.
