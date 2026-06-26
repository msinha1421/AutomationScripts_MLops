# AutomationScripts_MLops
The repo contains the scripts for MLops

## FileStorage.ps1

PowerShell script to migrate Azure File Shares from one storage account to another using Azure CLI and AzCopy.

## What It Does

- Validates storage account keys upfront before running any migrations
- Auto-creates missing file shares at the destination
- Generates temporary 5-day SAS tokens on the fly (no hardcoded SAS URIs)
- Runs AzCopy with `AZCOPY_CONCURRENCY_VALUE=512` for max throughput
- Uses `--overwrite=false` so existing files are never replaced

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) — installed and authenticated (`az login`)
- [AzCopy](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-v10) — installed and in your system PATH
- PowerShell 5.1+ (Windows PowerShell or PowerShell Core)

## Setup

### 1. Get Storage Account Access Keys

1. Go to [Azure Portal](https://portal.azure.com) → **Storage accounts**
2. Open the storage account → **Security + networking** → **Access keys**
3. Click **Show** next to key1 and copy it
4. Repeat for both source and destination accounts

### 2. Configure the Script

Open `FileStorage.ps1` and update the variables at the top:

```powershell
# Source
$srcAccount = "ffaimlstorage"
$srcKey     = "YOUR_SOURCE_ACCESS_KEY"

# Destination
$dstAccount = "gkffaimlstorage"
$dstKey     = "YOUR_DESTINATION_ACCESS_KEY"

# Shares to migrate
$shares = @(
    "poctest",
    "testshare",
    "training-checkpoint",
    "yotta-sync"
)
```

### 3. Run

```powershell
az login
.\FileStorage.ps1
```

## How It Works

1. **Validation** — Lists shares on both accounts to verify keys. Halts if either key is invalid.
2. **SAS Generation** — Creates Account-level SAS tokens scoped to File Services with read/write/list permissions.
3. **Destination Setup** — Creates each share at the destination if it doesn't exist. Skips with a warning if it does.
4. **AzCopy** — Copies files share-by-share. Prints a summary table of successes and failures at the end.

## Troubleshooting

| Problem | Fix |
|---|---|
| Script halts at validation | Access key is wrong — re-copy from Azure Portal |
| `azcopy: command not found` | AzCopy isn't in PATH — reinstall or add it |
| `az: command not found` | Azure CLI not installed |
| Network/firewall errors | Whitelist your machine in both storage account firewalls |
| Script stopped midway | Re-run it — `--overwrite=false` means it skips already-copied files |

## Security

> **Do not commit this file with keys populated.** Clear `$srcKey` and `$dstKey` before pushing.

- SAS tokens auto-expire after 5 days
- Rotate storage account keys after migration if they were shared or exposed


# Retro Report Automation : RetroML.y
RetroML — Jira Kanban Report Generator
An automated reporting tool that fetches your team's recent Jira tickets, analyzes performance metrics (story points, completion rates, estimate overruns, and blockers), and builds a beautiful, scannable HTML report.
The script can display the report locally in your browser or automatically push it directly to a centralized Confluence page for team retro alignment.

# Features

1. Automated Jira Fetching: Grabs all tickets updated within a rolling window (default: 14 days) via JQL, completely handling pagination.
2. Smart Metrics: Calculations for overall ticket completion rates, delivered story points, total time logged versus time estimated, and estimate overruns.
3. Highs & Lows Analysis: Automatically groups highlights (what went well) and issues/blockers (what needs improvement) side-by-side using a clean, Atlassian-inspired layout.
4. Action Item Generation: Auto-assigns pending action items based on current project bottlenecks (e.g., blocked tickets).
5. Confluence Integration: Pushes the finalized HTML template straight into an existing Confluence page utilizing Confluence Storage Format XHTML formatting.

# Setup & Installation

1. Prerequisites
Make sure you have Python 3.8+ installed.
2. Install Dependencies
Clone your script directory and install the required Atlassian and environment management libraries:
Bash
pip install atlassian-python-api python-dotenv
3. Configure the Environment
Create a .env file in the same directory as the script. Populate it with your Atlassian Cloud credentials and project details:

# Atlassian Instance Configuration
JIRA_URL="https://your-domain.atlassian.net"
CONFLUENCE_URL="https://your-domain.atlassian.net"
EMAIL="your-email@company.com"

# Generate your token at: https://id.atlassian.com/manage-profile/security/api-tokens
API_TOKEN="your_atlassian_api_token_here"

# Jira Project Settings
JIRA_PROJECT_KEY="PROJ"
DAYS_BACK=14

# Target Confluence Page Settings (Page must already be created/published)
CONFLUENCE_SPACE_KEY="TEAM"
CONFLUENCE_PAGE_TITLE="Team Kanban Retrospective Report"

# How to Use

The script operates in two modes: Local Preview and Confluence Live Push.
Mode 1: Local Preview (Safe Mode)
Generate the report data and check the visual outcome locally without changing anything in Confluence.
Bash
python RetroML.py
What happens: The script processes Jira data, saves a local report.html file, and automatically opens it up inside your default web browser.

Mode 2: Push to Confluence
Once you're satisfied with the data and layout, sync the live report directly to your team's Confluence document.
Bash
python RetroML.py --push
What happens: The script builds the report, displays your local preview, logs into Confluence, bumps the page history version, and updates the designated page with your fresh report template.

# Under the Hood

Custom Field Mapping
Jira instances occasionally store Story Points under varying custom fields depending on configuration. The script dynamically searches for standard story point tags in this order:
1. story_points
2. customfield_10016 (Default Jira Cloud Story Points field)
3. customfield_10028
