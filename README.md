# Databricks App Permission Management Tools

This repository contains scripts and a notebook to help manage Databricks app permissions, specifically addressing security concerns related to the **"Anyone in my organization can use"** permission setting. These tools provide workarounds for identifying and disabling organization-wide app access until this feature is addressed in the Databricks Apps roadmap.

## Background

When creating Databricks Apps, there is currently no way to disable the "Anyone in my organization can use" permission option through the UI. This can present security concerns for organizations that need to restrict app access to specific users or groups only. 

These scripts provide workarounds to:
1. **Audit** which apps have organization-wide access enabled
2. **Identify** apps with "account users" group permissions via API
3. **Remove** organization-wide permissions programmatically
4. **Monitor** permission changes over time

## Contents

### 1. SQL Query: `query_app_permissions.sql`

**Purpose**: Audit app permission changes using the System Table for audit logs.

**Description**: This SQL query examines the `system.access.audit` table to detect historical changes to app permissions, including when the "Anyone in my organization can use" option was enabled or modified.

**Usage**:
```sql
-- Run this query in a Databricks SQL warehouse or notebook
SELECT
  event_id,
  event_date,
  event_time,
  workspace_id,
  user_identity.email AS user,
  request_params.request_object_id AS app,
  request_params.access_control_list
FROM system.access.audit
WHERE action_name LIKE "changeAppsAcl"
ORDER BY event_time DESC;
```

**What it shows**:
- Who changed app permissions
- When the changes occurred
- Which apps were affected
- The complete access control list for each change

**Reference**: [Databricks Audit Logs - App Permission Changes](https://docs.databricks.com/aws/en/admin/system-tables/audit-logs#which-databricks-apps-have-been-updated-to-change-how-the-app-is-shared-with-other-users-or-groups)

---

### 2. Python Script: `app_permission_remove_any_user.py`

**Purpose**: Remove organization-wide access from all apps using the Databricks REST API.

**Description**: This Python script authenticates via OAuth, retrieves all apps in the workspace, identifies apps with "account users" group permissions (which represents "Anyone in my organization can use"), and removes those permissions.

**Prerequisites**:
- Service principal with OAuth credentials (client ID and secret)
- `CAN_MANAGE` permission on the apps you want to modify
- Python 3.7+ with `requests` library

**Setup**:
1. Create a service principal in your Databricks account
2. Grant the service principal appropriate permissions
3. Update the script with your credentials:
   ```python
   client_id = "your-client-id"
   client_secret = "your-client-secret"
   databricks_instance = "https://your-workspace.cloud.databricks.com"
   ```

**Usage**:
```bash
pip install requests
python app_permission_remove_any_user.py
```

**What it does**:
1. Authenticates using OAuth 2.0 client credentials flow
2. Retrieves list of all apps via `/api/2.0/apps`
3. For each app, gets current permissions via `/api/2.0/permissions/apps/{app_id}`
4. Filters out entries where `group_name == "account users"`
5. Updates permissions via PUT request, effectively removing org-wide access

**Reference**: [Databricks REST API - Set App Permissions](https://docs.databricks.com/api/workspace/apps/setpermissions#access_control_list)

---

### 3. Databricks Notebook: `disable_org_wide_access.ipynb`

**Purpose**: Comprehensive notebook to disable and manage organization-wide access using the Databricks SDK.

**Description**: This notebook offers a complete workflow with scanning, disabling, verification, and even revert capabilities.

**Prerequisites**:
- Access to a Databricks workspace
- `CAN_MANAGE` permission on apps
- Databricks Runtime (the notebook installs SDK automatically)

**Features**:
- ✅ **Scan**: Lists all apps with org-wide access enabled
- ✅ **Disable**: Removes "account users" group from ACLs
- ✅ **Verify**: Confirms changes were applied successfully
- ✅ **Revert**: Optional functionality to re-enable org-wide access if needed
- ✅ **Safety**: Requires explicit confirmation before making changes (`CONFIRM_DISABLE = True`)
- ✅ **Detailed Output**: Shows owner, status, and description for each app

**Usage**:
1. Import the notebook into your Databricks workspace
2. Run cells 1-4 to install dependencies and initialize the client
3. Run cells 5-8 to scan for apps with org-wide access
4. Review the list of affected apps
5. Set `CONFIRM_DISABLE = True` in cell 10
6. Run cells 11-14 to disable org-wide access and verify

**Key Functions**:
- `is_org_wide_enabled()` - Checks if an ACL entry is for "account users" with CAN_USE
- `get_all_org_wide_apps()` - Returns list of all apps with org-wide access
- `disable_org_wide_access()` - Removes "account users" from an app's ACL
- `enable_org_wide_access()` - (Optional) Re-enables org-wide access if needed

**Reference**: [Databricks Apps - Organization Permissions](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/permissions#organization-permissions)

---

## Security Considerations

### Why This Matters
The "Anyone in my organization can use" permission grants access to all users in your Databricks account, which may include:
- Users who shouldn't have access to sensitive data
- External contractors with account access
- Service principals with broad permissions

### Best Practices
1. **Principle of Least Privilege**: Only grant app access to users and groups that need it
2. **Regular Audits**: Use the SQL query regularly to monitor permission changes
3. **Access Reviews**: Periodically review app permissions and remove unnecessary access
4. **Explicit Permissions**: Use specific user or group grants instead of org-wide access
5. **Monitor Changes**: Set up alerts on the `system.access.audit` table for `changeAppsAcl` events

### What Changes When Disabling Org-Wide Access
**Before (with org-wide access)**:
- Permission setting: "Anyone in my organization can use"
- ACL contains entry: `{"group_name": "account users", "permission_level": "CAN_USE"}`
- **All** account users can access the app

**After (org-wide access disabled)**:
- Permission setting: "Only people with access can use"
- ACL no longer contains "account users" entry
- **Only** explicitly granted users/groups/service principals can access
- All other permissions (owners, specific users, specific groups) remain unchanged

---

## Comparison: Which Tool to Use?

| Feature | SQL Query | Python Script | Notebook |
|---------|-----------|---------------|----------|
| **Purpose** | Audit history | Bulk removal | Interactive workflow |
| **Authentication** | Workspace identity | OAuth (service principal) | Workspace identity |
| **Read-only** | ✅ Yes | ❌ No | ❌ No (with confirmation) |
| **Shows history** | ✅ Yes | ❌ No | ❌ No |
| **Modifies permissions** | ❌ No | ✅ Yes | ✅ Yes |
| **Verification** | ❌ No | ⚠️ Limited | ✅ Yes |
| **Revert capability** | ❌ No | ❌ No | ✅ Yes |
| **User-friendly** | ✅ SQL knowledge | ⚠️ Requires coding | ✅ Step-by-step |
| **Best for** | Compliance, auditing | CI/CD, automation | One-time fixes, exploration |

### Recommended Workflow
1. **Start with SQL query** to understand current state and history
2. **Use notebook** for interactive, one-time remediation with safety checks
3. **Use Python script** for automated enforcement in CI/CD pipelines

---

## Prerequisites

### General Requirements
- Databricks workspace (AWS, Azure, or GCP)
- Account administrator or workspace admin role (for audit queries)
- `CAN_MANAGE` permission on apps you want to modify

### For SQL Query
- Access to Unity Catalog
- Permissions to query `system.access.audit` table
- SQL warehouse or compute cluster

### For Python Script
- Python 3.7+
- `requests` library
- Service principal with OAuth credentials
- Network access to Databricks workspace

### For Notebook
- Databricks workspace
- Notebook execution permissions
- Databricks SDK will be installed automatically

---

## Installation & Setup

### Option 1: Clone Repository
```bash
git clone <repository-url>
cd helper-tools
```

### Option 2: Download Individual Files
Download the specific tool you need:
- `query_app_permissions.sql` - For auditing
- `app_permission_remove_any_user.py` - For automation
- `disable_org_wide_access.ipynb` - For interactive use

---

## Examples

### Example 1: Audit Current State
```sql
-- Find apps changed in the last 30 days
SELECT
  event_time,
  user_identity.email AS changed_by,
  request_params.request_object_id AS app_name,
  request_params.access_control_list
FROM system.access.audit
WHERE action_name = "changeAppsAcl"
  AND event_date >= current_date() - INTERVAL 30 DAYS
ORDER BY event_time DESC;
```

### Example 2: Check if Specific App Has Org-Wide Access
```python
import requests

# After authentication (see full script)
app_name = "my-app"
perm_url = f"{databricks_instance}/api/2.0/permissions/apps/{app_name}"
perm_response = requests.get(perm_url, headers=headers)
permissions = perm_response.json().get("access_control_list", [])

has_org_access = any(
    perm.get("group_name") == "account users" 
    for perm in permissions
)
print(f"Has org-wide access: {has_org_access}")
```

---

## Troubleshooting

### Common Issues

#### Issue: "Failed to get apps. Status: 403"
**Solution**: Ensure your service principal or user has appropriate permissions. You need at least `CAN_VIEW` on apps to list them.

#### Issue: "Failed to update permissions. Status: 403"
**Solution**: You need `CAN_MANAGE` permission on the app to modify its permissions. Contact the app owner or a workspace admin.

#### Issue: SQL query returns no results
**Solution**: 
- Verify Unity Catalog is enabled
- Check that `system.access.audit` table exists and is accessible
- Ensure you have the required permissions to query system tables
- Check if any apps exist in the workspace

#### Issue: Notebook fails with "Could not check app"
**Solution**: This is expected for apps you don't have permissions to view. The notebook will continue with other apps.

---

## Limitations

1. **No UI Toggle**: These are workarounds until Databricks adds a UI option to disable org-wide access
2. **Permission Required**: You must have `CAN_MANAGE` on each app to modify its permissions
3. **Not Preventative**: These tools remove existing org-wide access but don't prevent it from being re-enabled
4. **Manual Execution**: Requires manual or scheduled execution to maintain desired state

---

## Additional Resources

### Documentation
- [Databricks Apps - Organization Permissions](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/permissions#organization-permissions)
- [Set App Permissions API](https://docs.databricks.com/api/workspace/apps/setpermissions#access_control_list)
- [Audit Logs - App Permission Changes](https://docs.databricks.com/aws/en/admin/system-tables/audit-logs#which-databricks-apps-have-been-updated-to-change-how-the-app-is-shared-with-other-users-or-groups)
- [Databricks Apps Monitoring](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/monitor#monitor-app-permission-changes)

### API References
- [Apps API](https://docs.databricks.com/api/workspace/apps)
- [Permissions API](https://docs.databricks.com/api/workspace/apps/setpermissions)
- [Audit Logs System Table](https://docs.databricks.com/aws/en/admin/system-tables/audit-logs)

---

## Contributing

If you have improvements or find issues with these scripts, please:
1. Document the issue or enhancement
2. Test your changes thoroughly in a non-production environment
3. Submit updates with clear descriptions

---

## Disclaimer

These scripts are provided as-is to help manage app permissions until official product features are available. Always:
- Test in a non-production environment first
- Review changes before applying to production apps
- Maintain backups of your current permission configurations
- Verify changes after applying them

---

## License

[Include your license information here]

---

## Support

For issues related to:
- **These scripts**: [Your contact/support information]
- **Databricks Apps**: Contact Databricks Support
- **Feature requests**: Submit to Databricks product team

---

*Last updated: November 2025*

