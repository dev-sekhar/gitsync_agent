import { getGit, fetchRemote, getDiff, getCommitCount } from "../utils/git_utils";
import { logAction } from "../utils/logger";

export async function verifySync(localPath: string, branch: string) {
  try {
    const git = getGit(localPath);
    await fetchRemote(git, branch);
    
    const { behind, ahead } = await getCommitCount(git, branch);
    const diff = await getDiff(git, branch);
    
    const status = {
      behind,
      ahead,
      hasDiff: diff.length > 0,
      diff: diff.substring(0, 5000),
      isSynced: behind === 0 && ahead === 0 && diff.length === 0
    };

    await logAction("Sync Verification", "Success", status);
    return status;
  } catch (error: any) {
    await logAction("Sync Verification", "Failure", { error: error.message });
    throw error;
  }
}
