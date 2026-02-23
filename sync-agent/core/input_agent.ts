import fs from "fs-extra";
import { getGit, checkIsRepo } from "../utils/git_utils";
import { logAction } from "../utils/logger";

export async function validateInputs(localPath: string, repoUrl: string, branch: string) {
  try {
    const exists = await fs.pathExists(localPath);
    if (!exists) throw new Error(`Path does not exist: ${localPath}`);

    const git = getGit(localPath);
    const isRepo = await checkIsRepo(git);
    if (!isRepo) throw new Error(`Path is not a git repository: ${localPath}`);

    // Check remote connectivity
    await git.listRemote([repoUrl]);

    await logAction("Input Validation", "Success", { localPath, repoUrl, branch });
    return { success: true };
  } catch (error: any) {
    await logAction("Input Validation", "Failure", { error: error.message });
    throw error;
  }
}
