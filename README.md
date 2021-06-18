# reporting-jira-cloud
Script for extracting data from Jira Cloud API's for reporting purposes

# Dependencies
- Python 3.9
- See requirements.txt (use: pip install -r requirements.txt)

# Setup
Create an API Token against your Atlassian account and store it somewhere safe:
https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/

Edit jira_conf.yaml and set the url, user and token. These are the values speciific to your Jira instance, example:
```yaml
url: https://your-domain.atlassian.net/
user: me@example.com
token: my-api-token
```

To stop any changes to this file getting back into Git use:
```
git update-index --skip-worktree jira_conf.yaml
```

# Details

Extracts Jira ticket data based on a Jira Filter ID
* Completed work last month (10111)
* Completed work this month (10106)

Each search generates a separate .csv file in the data folder, using the description text for the filter in Jira as the file name.
To improve performance we currently only request the following fields in the search:
summary, status, created, resolutiondate, components, labels, issuetype, customfield_10023 (Time in Status), and customfield_10024 (Story Points)
The maximum result set is also limited to 999 tickets (maxResults=999).

For the completed work, using the command parameters, we also extract the days in specific status.

| Column | Description |
|---|---|
| To Do | Total days in "To Do" status |
| In Progress | Total days in "In Progress" status |
| Ready to Review | Total days in "Ready to Review" status |
| QA Test | Total days in "QA Test" status |
| Ready to Release | Total days in "Ready to Release" status |
| Days Open | Total lead time (Created -> Resolved) |

The days calculation for the status transitions include weekends and is rounded to 2 decimal places.

# Run
"py extract.py" - generates separate csv files with basic summary columns ("Key", "Summary", "Category", "Team", "Status", "Created", "Resolved")

"py extract.py all" - combines completed issues for this month and last month in one csv with detailed view columns ("Issue Type", "Story Points", "Days Open", "To Do", "In Progress", "Ready for Review", "QA Test", "Ready to Release")