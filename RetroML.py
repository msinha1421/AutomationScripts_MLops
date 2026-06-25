import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from atlassian import Jira, Confluence
 
# ── Load .env ─────────────────────────────────────────────────────────────────
load_dotenv()
 
# ── Config ────────────────────────────────────────────────────────────────────
JIRA_URL         = os.environ["JIRA_URL"]
EMAIL            = os.environ["EMAIL"]
API_TOKEN        = os.environ["API_TOKEN"]
JIRA_PROJECT_KEY = os.environ["JIRA_PROJECT_KEY"]
DAYS_BACK        = int(os.environ.get("DAYS_BACK", 14))
 
CONFLUENCE_URL        = os.environ["CONFLUENCE_URL"]
CONFLUENCE_SPACE_KEY  = os.environ["CONFLUENCE_SPACE_KEY"]
CONFLUENCE_PAGE_TITLE = os.environ["CONFLUENCE_PAGE_TITLE"]
 
# ── Push to Confluence flag ───────────────────────────────────────────────────
PUSH_TO_CONFLUENCE = "--push" in sys.argv
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Clients
# ─────────────────────────────────────────────────────────────────────────────
 
def get_jira_client() -> Jira:
    return Jira(url=JIRA_URL, username=EMAIL, password=API_TOKEN, cloud=True)
 
 
def get_confluence_client() -> Confluence:
    return Confluence(url=CONFLUENCE_URL, username=EMAIL, password=API_TOKEN, cloud=True)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Jira fetch
# ─────────────────────────────────────────────────────────────────────────────
 
def get_issues(jira: Jira) -> list[dict]:
    jql = (
        f'project = "{JIRA_PROJECT_KEY}" '
        f'AND updated >= -{DAYS_BACK}d '
        f'AND issuetype != Epic '
        f'ORDER BY updated DESC'
    )
    print(f"   JQL: {jql}")
 
    fields = (
        "summary,status,assignee,priority,"
        "story_points,customfield_10016,"
        "timeoriginalestimate,timespent,timeestimate,issuetype"
    )
 
    issues, start, batch = [], 0, 50
    while True:
        result = jira.jql(jql, fields=fields, start=start, limit=batch)
        issues.extend(result.get("issues", []))
        if start + batch >= result.get("total", 0):
            break
        start += batch
 
    return issues
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
 
def format_seconds(seconds) -> str:
    if not seconds:
        return "—"
    hours, minutes = seconds // 3600, (seconds % 3600) // 60
    if hours and minutes:
        return f"{hours}h {minutes}m"
    return f"{hours}h" if hours else f"{minutes}m"
 
 
def get_sp(fields: dict) -> float:
    sp = (
        fields.get("story_points")
        or fields.get("customfield_10016")
        or fields.get("customfield_10028")
    )
    return float(sp) if sp is not None else 0.0
 
 
def badge(text: str, bg: str, fg: str) -> str:
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 7px;'
        f'border-radius:3px;font-size:11px;font-weight:600;">{text}</span>'
    )
 
 
def status_badge(status: str) -> str:
    colours = {
        "To Do":        ("#DFE1E6", "#42526E"),
        "In Progress":  ("#DEEBFF", "#0052CC"),
        "In Review":    ("#EAE6FF", "#403294"),
        "Done":         ("#E3FCEF", "#006644"),
        "Blocked":      ("#FFEBE6", "#BF2600"),
    }
    bg, fg = colours.get(status, ("#F4F5F7", "#42526E"))
    return badge(status, bg, fg)
 
 
def mini_table(rows_html: str, headers: list[str]) -> str:
    th = "".join(
        f'<th style="padding:5px 8px;text-align:left;font-size:11px;font-weight:600;'
        f'color:#5E6C84;background:#F4F5F7;border-bottom:1px solid #DFE1E6;">{h}</th>'
        for h in headers
    )
    return (
        f'<table style="border-collapse:collapse;width:100%;font-size:12px;">'
        f'<thead><tr>{th}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table>'
    )
 
 
def td(content: str, center: bool = False) -> str:
    align = "center" if center else "left"
    return (
        f'<td style="padding:5px 8px;border-bottom:1px solid #DFE1E6;'
        f'text-align:{align};vertical-align:middle;">{content}</td>'
    )
 
 
def section_label(text: str) -> str:
    return (
        f'<p style="font-size:11px;font-weight:700;color:#5E6C84;'
        f'text-transform:uppercase;letter-spacing:0.05em;margin:0 0 6px 0;">{text}</p>'
    )
 
def bullet(dot_color: str, text: str, tag_text: str, tag_bg: str, tag_fg: str) -> str:
    return (
        f'<table style="border-collapse:collapse;width:100%;margin-bottom:5px;">'
        f'<tr>'
        f'<td style="width:12px;vertical-align:top;padding-top:4px;">'
        f'<span style="width:7px;height:7px;border-radius:50%;background:{dot_color};display:inline-block;"></span>'
        f'</td>'
        f'<td style="font-size:12px;color:#172B4D;vertical-align:top;padding-right:8px;">{text}</td>'
        f'<td style="width:60px;text-align:right;vertical-align:top;">'
        f'<span style="font-size:10px;font-weight:600;padding:1px 6px;border-radius:3px;'
        f'background:{tag_bg};color:{tag_fg};white-space:nowrap;">{tag_text}</span>'
        f'</td>'
        f'</tr>'
        f'</table>'
    )
 
 
def metric_card(label: str, value: str, sub: str = "") -> str:
    sub_html = (
        f'<div style="font-size:10px;color:#6B778C;margin-top:1px;">{sub}</div>'
        if sub else ""
    )
    return (
        f'<td style="padding:6px 8px;">'
        f'<div style="background:#F4F5F7;border-radius:4px;padding:8px 10px;">'
        f'<div style="font-size:11px;color:#6B778C;margin-bottom:2px;">{label}</div>'
        f'<div style="font-size:18px;font-weight:600;color:#172B4D;">{value}</div>'
        f'{sub_html}</div></td>'
    )
 
 
# ─────────────────────────────────────────────────────────────────────────────
# HTML builder
# ─────────────────────────────────────────────────────────────────────────────
 
def build_page(issues: list[dict]) -> str:
    now          = datetime.now().strftime("%d %b %Y, %H:%M")
    report_label = f"Last {DAYS_BACK} days"
 
    done_statuses = {"Done", "Closed", "Resolved"}
    done_issues   = [i for i in issues if i["fields"]["status"]["name"] in done_statuses]
    open_issues   = [i for i in issues if i["fields"]["status"]["name"] not in done_statuses]
    blocked       = [i for i in issues if i["fields"]["status"]["name"] == "Blocked"]
 
    total_est    = sum(i["fields"].get("timeoriginalestimate") or 0 for i in issues)
    total_logged = sum(i["fields"].get("timespent") or 0 for i in issues)
    total_sp     = sum(get_sp(i["fields"]) for i in issues)
    done_sp      = sum(get_sp(i["fields"]) for i in done_issues)
    completion   = round(len(done_issues) / len(issues) * 100) if issues else 0
 
    overruns = [
        i for i in issues
        if (i["fields"].get("timespent") or 0)
            > (i["fields"].get("timeoriginalestimate") or 0) * 1.2
        and (i["fields"].get("timeoriginalestimate") or 0) > 0
    ]
 
    # ── Tables ────────────────────────────────────────────────────────────────
    done_rows = ""
    for i in done_issues[:8]:
        f, key = i["fields"], i["key"]
        sp = get_sp(f)
        done_rows += (
            "<tr>"
            + td(f'<a href="{JIRA_URL}/browse/{key}" style="color:#0052CC;font-weight:600;">{key}</a>')
            + td(f.get("summary", "")[:100])
            + td(str(int(sp)) if sp else "—", center=True)
            + td(format_seconds(f.get("timespent")), center=True)
            + "</tr>"
        )
    done_table = mini_table(done_rows, ["Key", "Summary", "SP", "Logged"])
 
    open_rows = ""
    for i in open_issues[:8]:
        f, key = i["fields"], i["key"]
        open_rows += (
            "<tr>"
            + td(f'<a href="{JIRA_URL}/browse/{key}" style="color:#0052CC;font-weight:600;">{key}</a>')
            + td(f.get("summary", "")[:40])
            + td(status_badge(f["status"]["name"]))
            + td(format_seconds(f.get("timeestimate")), center=True)
            + "</tr>"
        )
    open_table = mini_table(open_rows, ["Key", "Summary", "Status", "Remaining"])
 
    overrun_rows = ""
    for i in overruns[:5]:
        f, key = i["fields"], i["key"]
        overrun_rows += (
            "<tr>"
            + td(f'<a href="{JIRA_URL}/browse/{key}" style="color:#0052CC;font-weight:600;">{key}</a>')
            + td(f.get("summary", "")[:38])
            + td(format_seconds(f.get("timeoriginalestimate")), center=True)
            + td(f'<span style="color:#BF2600;font-weight:600;">{format_seconds(f.get("timespent"))}</span>', center=True)
            + "</tr>"
        )
    if not overrun_rows:
        overrun_rows = '<tr><td colspan="4" style="padding:8px;color:#6B778C;font-size:12px;text-align:center;">No overruns</td></tr>'
    overrun_table = mini_table(overrun_rows, ["Key", "Summary", "Estimated", "Actual"])
 
    # ── Bullets ───────────────────────────────────────────────────────────────
    hi_bullets = ""
    if completion >= 70:
        hi_bullets += bullet("#1D9E75", f"{completion}% of tickets completed in this period", "Quality", "#E3FCEF", "#006644")
    if done_sp > 0:
        hi_bullets += bullet("#1D9E75", f"{int(done_sp)} story points delivered", "Quality", "#E3FCEF", "#006644")
    if not blocked:
        hi_bullets += bullet("#1D9E75", "No blocked tickets in this period", "Process", "#DEEBFF", "#0052CC")
    if total_logged <= total_est and total_est > 0:
        hi_bullets += bullet("#1D9E75", "Team stayed within time estimates overall", "Process", "#DEEBFF", "#0052CC")
    if len(done_issues) >= len(open_issues) * 2:
        hi_bullets += bullet("#1D9E75", f"{len(done_issues)} tickets done vs {len(open_issues)} still open", "People", "#EAE6FF", "#403294")
    if not hi_bullets:
        hi_bullets = bullet("#1D9E75", "Period complete — review highlights with the team", "General", "#F4F5F7", "#42526E")
 
    lo_bullets = ""
    if blocked:
        lo_bullets += bullet("#D85A30", f"{len(blocked)} ticket(s) blocked — review access and dependencies", "Process", "#DEEBFF", "#0052CC")
    if overruns:
        lo_bullets += bullet("#D85A30", f"{len(overruns)} ticket(s) exceeded time estimates by more than 20%", "Process", "#DEEBFF", "#0052CC")
    if open_issues:
        lo_bullets += bullet("#D85A30", f"{len(open_issues)} ticket(s) still in progress or not started", "Process", "#DEEBFF", "#0052CC")
    if completion < 70:
        lo_bullets += bullet("#D85A30", f"Completion rate {completion}% — below 70% target", "Quality", "#E3FCEF", "#006644")
    if total_logged > total_est * 1.1 and total_est > 0:
        lo_bullets += bullet("#D85A30", "Team logged more hours than estimated overall", "People", "#EAE6FF", "#403294")
    if not lo_bullets:
        lo_bullets = bullet("#D85A30", "No major issues — note any process concerns with the team", "General", "#F4F5F7", "#42526E")
 
    # ── Action items ──────────────────────────────────────────────────────────
    action_rows = ""
    seen_owners: set[str] = set()
    for i in blocked[:3]:
        f, key   = i["fields"], i["key"]
        assignee = (f.get("assignee") or {}).get("displayName", "Team")
        if assignee not in seen_owners:
            seen_owners.add(assignee)
            action_rows += "<tr>" + td(f"Unblock {key} — resolve access/dependency issue") + td(assignee) + td(badge("Open", "#FFEBE6", "#BF2600")) + "</tr>"
    if overruns:
        action_rows += "<tr>" + td("Review estimate accuracy for overrun tickets") + td("Team Lead") + td(badge("Open", "#FFEBE6", "#BF2600")) + "</tr>"
    if open_issues:
        action_rows += "<tr>" + td(f"Follow up on {len(open_issues)} open ticket(s)") + td("Team Lead") + td(badge("Open", "#FFEBE6", "#BF2600")) + "</tr>"
    if not action_rows:
        action_rows = '<tr><td colspan="3" style="padding:8px;color:#6B778C;font-size:12px;text-align:center;">No action items — add manually if needed</td></tr>'
    action_table = mini_table(action_rows, ["Action", "Owner", "Status"])
 
    hi_cell = "vertical-align:top;padding:14px 16px;width:50%;border-right:1px solid #DFE1E6;"
    lo_cell = "vertical-align:top;padding:14px 16px;width:50%;"
 
    return f"""
<h2 style="color:#172B4D;font-size:20px;margin-bottom:4px;">
  Kanban Report — {report_label}
</h2>
<p style="color:#6B778C;font-size:12px;margin-bottom:20px;">
  Generated: {now} &nbsp;|&nbsp; Project: <b>{JIRA_PROJECT_KEY}</b> &nbsp;|&nbsp;
  Total tickets: <b>{len(issues)}</b> &nbsp;|&nbsp;
  <a href="{JIRA_URL}/jira/software/projects/{JIRA_PROJECT_KEY}/boards">View board in Jira</a>
</p>
 
<table style="border-collapse:collapse;width:100%;margin-bottom:16px;">
  <tr>
    {metric_card("Tickets done", str(len(done_issues)), f"of {len(issues)} total")}
    {metric_card("Completion", f"{completion}%", f"last {DAYS_BACK} days")}
    {metric_card("SP delivered", str(int(done_sp)), f"of {int(total_sp)} total")}
    {metric_card("Time logged", format_seconds(total_logged), f"of {format_seconds(total_est)} est.")}
  </tr>
</table>
 
<table style="border-collapse:collapse;width:100%;border:1px solid #DFE1E6;">
  <thead>
    <tr>
      <th style="padding:10px 16px;background:#E3FCEF;color:#006644;font-size:14px;font-weight:700;border-bottom:1px solid #ABF5D1;border-right:1px solid #DFE1E6;width:50%;text-align:left;">
        &#x1F4C8; Highs — what went well
      </th>
      <th style="padding:10px 16px;background:#FFEBE6;color:#BF2600;font-size:14px;font-weight:700;border-bottom:1px solid #FFBDAD;width:50%;text-align:left;">
        &#x1F4C9; Lows — what needs improvement
      </th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="{hi_cell}">
        {section_label("Highlights")}
        {hi_bullets}
        <br/>
        {section_label("Completed tickets")}
        {done_table}
      </td>
      <td style="{lo_cell}">
        {section_label("Issues identified")}
        {lo_bullets}
        <br/>
        {section_label("Open &amp; blocked tickets")}
        {open_table}
        <br/>
        {section_label("Estimate overruns")}
        {overrun_table}
        <br/>
        {section_label("Action items")}
        {action_table}
      </td>
    </tr>
  </tbody>
</table>
 
<p style="color:#6B778C;font-size:11px;margin-top:12px;">
  Auto-generated by RetroML.py
</p>
"""
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Save HTML and open in browser
# ─────────────────────────────────────────────────────────────────────────────
 
def save_html(html_body: str) -> Path:
    output_path = Path("report.html")
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Kanban Report — {JIRA_PROJECT_KEY}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:#F4F5F7; margin:0; padding:32px; color:#172B4D; }}
    .page {{ max-width:1100px; margin:0 auto; background:#fff; border-radius:8px; border:1px solid #DFE1E6; padding:32px 40px; }}
    a {{ color:#0052CC; }}
  </style>
</head>
<body>
  <div class="page">
    {html_body}
  </div>
</body>
</html>"""
    output_path.write_text(full_html, encoding="utf-8")
    return output_path
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Confluence push
# ─────────────────────────────────────────────────────────────────────────────
 
def update_confluence_page(html_body: str) -> None:
    print("🔄 Connecting to Confluence...")
    confluence = get_confluence_client()
 
    print(f"🔄 Looking for page '{CONFLUENCE_PAGE_TITLE}' in space '{CONFLUENCE_SPACE_KEY}'...")
    page = confluence.get_page_by_title(
        space=CONFLUENCE_SPACE_KEY,
        title=CONFLUENCE_PAGE_TITLE
    )
 
    if not page:
        raise ValueError(
            f"❌  Page '{CONFLUENCE_PAGE_TITLE}' not found in space '{CONFLUENCE_SPACE_KEY}'.\n"
            f"    Make sure the page is published (not draft) and the title matches exactly."
        )
 
    page_id     = page["id"]
    current_ver = page.get("version", {}).get("number", 1)
 
    confluence.update_page(
    page_id=page_id,
    title=CONFLUENCE_PAGE_TITLE,
    body=html_body,
    representation="storage",
    minor_edit=False
    )
 
    print(f"✅ Confluence page updated! (version {current_ver + 1})")
    print(f"   → {CONFLUENCE_URL}/wiki/spaces/{CONFLUENCE_SPACE_KEY}/pages/{page_id}")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
 
def main() -> None:
    print("🔄 Connecting to Jira...")
    jira = get_jira_client()
 
    print(f"🔄 Fetching tickets updated in the last {DAYS_BACK} days...")
    issues = get_issues(jira)
 
    if not issues:
        print(f"⚠️  No tickets found for project '{JIRA_PROJECT_KEY}' in the last {DAYS_BACK} days.")
        print(f"   Try increasing DAYS_BACK (currently {DAYS_BACK}) in your .env.")
        sys.exit(0)
 
    print(f"✅ Found {len(issues)} tickets")
 
    print("🔄 Building HTML report...")
    html = build_page(issues)
 
    path = save_html(html)
    print(f"✅ Report saved → {path.resolve()}")
    print("   Opening in browser...")
    webbrowser.open(path.resolve().as_uri())
 
    if PUSH_TO_CONFLUENCE:
        update_confluence_page(html)
        print("\n🎉 Done! Report is live in Confluence.")
    else:
        print("\n💡 Happy with the report? Run with --push to send it to Confluence:")
        print(f"   python RetroML.py --push")
 
 
if __name__ == "__main__":
    main()
 