from tiger_client import get_conn, insert_tool, insert_action, insert_system

conn = get_conn()

# Seed Tools
insert_tool(conn, {"tool_id": "t1", "tool_name": "github_api", "risk_level": 0.7})
insert_tool(conn, {"tool_id": "t2", "tool_name": "terraform_cli", "risk_level": 0.9})

# Seed Actions
insert_action(conn, {"action_id": "ac1", "action_name": "delete_repo", "severity": 0.8})
insert_action(conn, {"action_id": "ac2", "action_name": "destroy_infra", "severity": 0.95})
insert_action(conn, {"action_id": "ac3", "action_name": "read_repo", "severity": 0.1})

# Seed Systems
insert_system(conn, {"system_id": "s1", "system_name": "prod_db", "criticality": 1.0})
insert_system(conn, {"system_id": "s2", "system_name": "github_repo", "criticality": 0.6})
insert_system(conn, {"system_id": "s3", "system_name": "terraform_infra", "criticality": 0.9})

print("✅ Seed data inserted successfully!")
