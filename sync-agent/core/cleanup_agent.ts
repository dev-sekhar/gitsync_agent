import fs from "fs-extra";
import { logAction } from "../utils/logger";

export async function cleanupLocal(localPath: string, confirmed: boolean) {
  try {
    if (!confirmed) throw new Error("Deletion not confirmed");

    await fs.remove(localPath);
    
    await logAction("Cleanup", "Success", { localPath });
    return { success: true };
  } catch (error: any) {
    await logAction("Cleanup", "Failure", { error: error.message });
    throw error;
  }
}
