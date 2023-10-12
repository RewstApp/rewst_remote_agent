## Sign-Up Process Plan

When: config.json does not exist

How:
* Rewst Workflow @ Rewst Staff (top) level of Rewst
  * Shortened URL points to the webhook trigger.
  * Call it `$config_url` for this document
  
Run: 
* `rewst_remote_agent[.exe] --configure --org_id <org_id> --org_secret <secret_org_var>`

Process:
* Makes POST to `$config_url`

```json
{
  "org_id": "$org_id",
  "org_secret": "$org_secret",
  "hostname": "$computer_hostname",
  "agent_version": "$version_number_from_agent"
}
```  

* Build `config.json`:
```json
{
}
```

* Saves `config.json` to:
  * Windows: `C:\programdata\rewst_remote_agent\config.json`
  * Linux / Darwin:
    *  `/etc/rewst_remote_agent/config.json`
    *  `chmod 600`
      
