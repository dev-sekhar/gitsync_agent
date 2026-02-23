import fs from "fs-extra";
import path from "path";

const LOG_FILE = path.join(process.cwd(), "sync-agent", "audit", "sync_agent_audit.log");

export interface AuditEntry {
  timestamp: string;
  action: string;
  result: string;
  details?: any;
}

export async function logAction(action: string, result: string, details?: any) {
  const entry: AuditEntry = {
    timestamp: new Date().toISOString(),
    action,
    result,
    details,
  };
  
  const logDir = path.dirname(LOG_FILE);
  await fs.ensureDir(logDir);
  
  const logLine = JSON.stringify(entry) + "\n";
  await fs.appendFile(LOG_FILE, logLine);
  console.log(`[AUDIT] ${action}: ${result}`);
}

export async function getLogs(): Promise<AuditEntry[]> {
  if (!(await fs.pathExists(LOG_FILE))) return [];
  const content = await fs.readFile(LOG_FILE, "utf-8");
  return content
    .trim()
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}
