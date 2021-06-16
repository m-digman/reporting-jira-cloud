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

# Run
