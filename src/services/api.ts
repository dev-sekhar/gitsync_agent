export interface AuditLog {
  timestamp: string;
  action: string;
  result: string;
  details?: any;
}

export interface SyncStatus {
  behind: number;
  ahead: number;
  hasDiff: boolean;
  diff: string;
  isSynced: boolean;
}

export const api = {
  async getLogs(): Promise<AuditLog[]> {
    const res = await fetch("/api/logs");
    return res.json();
  },

  async ls(dir?: string): Promise<{ currentPath: string; parentPath: string; directories: { name: string; path: string }[] }> {
    const url = dir ? `/api/ls?dir=${encodeURIComponent(dir)}` : "/api/ls";
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to list directories");
    return res.json();
  },

  async init(localPath: string, repoUrl: string, branch: string) {
    const res = await fetch("/api/init", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ localPath, repoUrl, branch }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Initialization failed");
    }
    return res.json();
  },

  async verify(localPath: string, branch: string): Promise<SyncStatus> {
    const res = await fetch("/api/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ localPath, branch }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Verification failed");
    }
    return res.json();
  },

  async updateReadme(localPath: string, branch: string, summary: string) {
    const res = await fetch("/api/update-readme", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ localPath, branch, summary }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "README update failed");
    }
    return res.json();
  },

  async deleteFolder(localPath: string, confirmed: boolean) {
    const res = await fetch("/api/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ localPath, confirmed }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Deletion failed");
    }
    return res.json();
  },
};
