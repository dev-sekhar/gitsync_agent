import fs from "fs-extra";
import path from "path";
import { getGit } from "../utils/git_utils";
import { logAction } from "../utils/logger";

export async function updateReadme(localPath: string, branch: string, summary: string) {
  try {
    const git = getGit(localPath);
    const readmePath = path.join(localPath, "README.md");
    
    const timestamp = new Date().toLocaleString();
    const syncNote = `\n\n---\n**Agent Sync Confirmation**\n- Timestamp: ${timestamp}\n- Status: Synchronized\n- Summary: ${summary}\n`;
    
    if (await fs.pathExists(readmePath)) {
      await fs.appendFile(readmePath, syncNote);
    } else {
      await fs.writeFile(readmePath, `# Project\n${syncNote}`);
    }

    await git.add("README.md");
    const commitMsg = `Agent update: README sync confirmation [${timestamp}]`;
    await git.commit(commitMsg);
    await git.push("origin", branch);

    await logAction("README Update", "Success", { commitMsg });
    return { success: true };
  } catch (error: any) {
    await logAction("README Update", "Failure", { error: error.message });
    throw error;
  }
}
