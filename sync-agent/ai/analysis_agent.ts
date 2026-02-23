import { GoogleGenAI } from "@google/genai";
import { logAction } from "../utils/logger";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || "" });

export async function analyzeDiff(diff: string) {
  if (!diff || diff.trim() === "") return "No changes detected. Local and remote are perfectly synchronized.";

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: `Summarize the following git diff in a human-friendly way. Focus on what was changed, added, or removed. Keep it concise (2-3 sentences).
      
      DIFF:
      ${diff}`,
    });

    const summary = response.text || "Could not generate summary.";
    await logAction("Diff Analysis", "Success", { summary });
    return summary;
  } catch (error: any) {
    await logAction("Diff Analysis", "Failure", { error: error.message });
    return "Error generating AI summary.";
  }
}
