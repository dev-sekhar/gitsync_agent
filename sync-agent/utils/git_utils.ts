import { simpleGit, SimpleGit } from "simple-git";

export function getGit(localPath: string): SimpleGit {
  return simpleGit(localPath);
}

export async function checkIsRepo(git: SimpleGit): Promise<boolean> {
  return await git.checkIsRepo();
}

export async function fetchRemote(git: SimpleGit, branch: string): Promise<void> {
  await git.fetch("origin", branch);
}

export async function getDiff(git: SimpleGit, branch: string): Promise<string> {
  return await git.diff([`origin/${branch}`, branch]);
}

export async function getCommitCount(git: SimpleGit, branch: string): Promise<{ behind: number; ahead: number }> {
  const count = await git.raw(["rev-list", "--left-right", "--count", `origin/${branch}...${branch}`]);
  const [behind, ahead] = count.trim().split("\t").map(Number);
  return { behind, ahead };
}
