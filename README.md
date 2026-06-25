# AutomationScripts_MLops
The repo contains the scripts for MLops

# Azure File Share Migration Script : FileStorage.ps1
This PowerShell script automates the migration of multiple Azure File Shares from a source storage account to a destination storage account using az cli and azcopy.
It handles upfront credential verification, dynamically generates short-lived SAS tokens for secure transfer, pre-creates missing shares at the destination, and optimizes copy speeds for large datasets.

# Features:

1. Upfront Verification: Validates storage account keys before running any migrations, avoiding mid-job failures.
2. Automated Provisioning: Checks if the target file share exists at the destination; if not, it automatically creates it.
3. Secure Token Generation: Generates temporary 5-day Account SAS tokens on the fly, eliminating the need to hardcode SAS URIs.
4. Performance Tuned: Sets AZCOPY_CONCURRENCY_VALUE = 512 to maximize network throughput for file intensive copies.
5. Safe Copy Mode: Uses --overwrite=false to ensure existing files at the destination are never accidentally replaced or corrupted.

# Prerequisites

Before running the script, ensure you have the following tools installed and configured:
1. Azure CLI: Installed and authenticated (az login). Download here.
2. AzCopy: Installed and added to your system's PATH. Download here.
3. PowerShell: 5.1 or higher (Windows PowerShell or PowerShell Core).

Configuration
Open the script and update the variables at the top of the file:

PowerShell
# 1. Define your source and destination accounts
$srcAccount = "ffaimlstorage"
$srcKey     = "YOUR_SOURCE_ACCESS_KEY"

$dstAccount = "gkffaimlstorage"
$dstKey     = "YOUR_DESTINATION_ACCESS_KEY"

# 2. Add the specific share names you want to migrate
$shares = @(
    "poctest",
    "testshare",
    "training-checkpoint",
    "yotta-sync"
)

# How It Works
1. Validation
Step 1
The script attempts to list file shares on both accounts using the provided keys. If either key is invalid, the script safely halts execution immediately.

2. SAS Token Generation
Step 2
It generates an Account-level Shared Access Signature (SAS) for both source and destination scoped explicitly to File Services (f) with full read/write/list permissions.

3. Destination Setup
Step 3
It loops through your array of shares. For each share, it attempts to create it at the destination. If the share already exists, it gracefully logs a warning and moves forward.

4. AzCopy Execution
Step 4
It constructs the secure source and destination URIs and invokes azcopy copy. A summary table logs successful and failed shares at the very end.


# Troubleshooting & Safety
1. Important Security Reminder: Never commit this script to a public repository with your $srcKey or $dstKey populated. Always clear the keys before pushing to source control.
2. Network Firewalls: If either storage account has "Enabled from selected networks and IP addresses" turned on, ensure the machine running this script is whitelisted in both storage firewalls.
3. Resuming Interrupted Jobs: If the script stops halfway through, you can safely run it again. Because --overwrite=false is set, AzCopy will skip files that are already completed and only copy missing/remaining data.



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
