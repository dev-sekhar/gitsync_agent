import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import fs from "fs-extra";
import { fileURLToPath } from "url";

// Agent Imports
import { validateInputs } from "./sync-agent/core/input_agent";
import { verifySync } from "./sync-agent/core/sync_agent";
import { updateReadme } from "./sync-agent/core/update_agent";
import { cleanupLocal } from "./sync-agent/core/cleanup_agent";
import { analyzeDiff } from "./sync-agent/ai/analysis_agent";
import { getLogs } from "./sync-agent/utils/logger";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;

app.use(express.json());

// API Routes mapped to Agents
app.get("/api/logs", async (req, res) => {
  try {
    const logs = await getLogs();
    res.json(logs.reverse());
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.get("/api/ls", async (req, res) => {
  const { dir = process.cwd() } = req.query;
  try {
    const absolutePath = path.resolve(dir as string);
    const files = await fs.readdir(absolutePath, { withFileTypes: true });
    const directories = files
      .filter((f) => f.isDirectory())
      .map((f) => ({
        name: f.name,
        path: path.join(absolutePath, f.name),
      }));
    
    res.json({
      currentPath: absolutePath,
      parentPath: path.dirname(absolutePath),
      directories,
    });
  } catch (error: any) {
    res.status(400).json({ error: error.message });
  }
});

app.post("/api/init", async (req, res) => {
  const { localPath, repoUrl, branch = "dev" } = req.body;
  try {
    await validateInputs(localPath, repoUrl, branch);
    res.json({ success: true });
  } catch (error: any) {
    res.status(400).json({ error: error.message });
  }
});

app.post("/api/verify", async (req, res) => {
  const { localPath, branch = "dev" } = req.body;
  try {
    const status = await verifySync(localPath, branch);
    res.json(status);
  } catch (error: any) {
    res.status(400).json({ error: error.message });
  }
});

app.post("/api/update-readme", async (req, res) => {
  const { localPath, branch = "dev", summary } = req.body;
  try {
    await updateReadme(localPath, branch, summary);
    res.json({ success: true });
  } catch (error: any) {
    res.status(400).json({ error: error.message });
  }
});

app.post("/api/delete", async (req, res) => {
  const { localPath, confirmed } = req.body;
  try {
    await cleanupLocal(localPath, confirmed);
    res.json({ success: true });
  } catch (error: any) {
    res.status(400).json({ error: error.message });
  }
});

async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.join(__dirname, "dist")));
    app.get("*", (req, res) => {
      res.sendFile(path.join(__dirname, "dist", "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
