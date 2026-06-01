# Klaviyo MCP — tool reference

The Klaviyo MCP (`https://mcp.klaviyo.com/mcp`) gives this plugin direct API access to the Ahipoki Klaviyo account once Anas provisions it. Use these tools instead of Chrome navigation wherever possible.

## Available tool surface (27+ tools)

Confirmed from the MCP registry:

- `get_account_details` — account-level info
- `get_campaigns` — list all campaigns with filters
- `get_campaign` — single campaign detail
- `create_campaign` — programmatic campaign creation
- `assign_template_to_campaign_message` — wire a template to a campaign
- `get_catalog_items` — product catalog (useful for Ahipoki menu items)
- `get_events` — customer behavior events
- `get_metrics` — open / click / order metrics
- (and 19 more — fetch with `mcp__plugin_marketing_klaviyo__*` once installed and explore)

## How each retention skill should use the Klaviyo MCP

### `klaviyo-migration`

- **Provisioning check**: `get_account_details` to confirm the account is live and Spice has admin
- **Flow status**: `get_campaigns` filtered by flow type to see which Thanx flows have been ported
- **Performance comparison**: `get_metrics` for ported flows vs Thanx baseline (last 30 days each)
- **Campaign creation during migration**: `create_campaign` + `assign_template_to_campaign_message` to spin up the first Klaviyo campaign for Ahipoki without leaving chat

### `retention-monthly-report` (for Ahipoki post-migration)

- **List all campaigns sent in month**: `get_campaigns` with date filter
- **Per-campaign performance**: `get_campaign` (campaign_id) for opens / clicks / revenue
- **Top-line metrics**: `get_metrics` for list growth, conversions, revenue per recipient
- **Customer events**: `get_events` for unsubscribe spikes, complaint flags

This replaces ~30 minutes of Chrome navigation per Ahipoki monthly report.

### `retention-flow-designer`

- **Create the flow's first campaign**: `create_campaign` with the brief's copy + segment
- **Pull catalog for menu-item callouts**: `get_catalog_items` to reference real SKUs
- **Confirm template availability**: `assign_template_to_campaign_message` after Dilli's design is uploaded

### `retention-campaign-brief`

- **Validate segment exists in Klaviyo**: query the segments endpoint
- **Auto-populate Campaign Planning DB with Klaviyo campaign ID** once created

## Fallback for Thanx + Toast

No Klaviyo MCP-equivalent exists for either platform. Continue using:
- Chrome MCP / Comet for dashboard navigation
- The `Toast Retention Data Pull Guide` and `Thanx Retention Data Pull Guide` in Notion for the manual paths

If Anas surfaces a Thanx-side API access during migration, revisit.

## Auth + access

The Klaviyo MCP uses OAuth. Each Spice operator authenticates their session individually. The account-level access is shared because it points to Ahipoki's single Klaviyo account.

Do not commit Klaviyo API keys to any file. Use the MCP OAuth flow exclusively.
